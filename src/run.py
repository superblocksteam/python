import sys, json, traceback
import importlib.util
from textwrap import indent
from plotly.graph_objects import Figure as PlotlyFigure
from plotly.utils import PlotlyJSONEncoder
import re
import simplejson as sjson


class SuperblocksObject(dict):
    """Wrapper around dict that provides dot.notation access to dictionary attributes"""

    def __getattr__(self, key):
        try:
            if type(self[key]) == dict:
                return SuperblocksObject(self[key])
            elif type(self[key]) == list:
                return SuperblocksList(self[key])
            else:
                return self[key]

        except KeyError as k:
            raise AttributeError(f"object has no attribute {k}")

    def __getitem__(self, key):
        cur_item = dict.__getitem__(self, key)
        if type(cur_item) == dict:
            return SuperblocksObject(cur_item)
        elif type(cur_item) == list:
            return SuperblocksList(cur_item)
        else:
            return cur_item

    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    @property
    def __dict__(self):
        return self


class SuperblocksList(list):
    def __getitem__(self, n):
        cur_item = list.__getitem__(self, n)
        if type(cur_item) == dict:
            return SuperblocksObject(cur_item)
        elif type(cur_item) == list:
            return SuperblocksList(cur_item)
        else:
            return cur_item


sharedCode = f"""
from functools import partial
import base64
import requests
import io

# TODO(frank): I don't think we should be exposing this.
#              However, I don't know how not to as I don't
#              think you can inline functions in python.
def superblocksReader(name, path, mode=None):
    def serialize(f, name, mode=None):
        # https://stackoverflow.com/questions/898669/how-can-i-detect-if-a-file-is-binary-non-text-in-python
        textchars = bytearray({{7,8,9,10,12,13,27}} | set(range(0x20, 0x100)) - {{0x7f}})
        is_binary_string = lambda bytes: bool(bytes.translate(None, textchars))
        bytes = f.read(1024)
        f.seek(0)
        if mode == 'binary' or is_binary_string(bytes):
            if mode == 'text':
                raise ValueError(f"File {{name}} has binary data. Call .readContents(\'binary\') and then apply your own encoding")
            return base64.b64encode(f.read()).decode('ascii')
        if mode == 'binary':
            raise ValueError(f"File {{name}} is text. Call .readContents(\'text\') and then apply your own encoding like .encode(\'latin1\')")
        return f.read().decode('utf8')

    def fetchFromController(path):
        response = requests.get(
            f"{{globals()['$fileServerUrl']}}",
            stream = True,
            params={{
                'location': path
            }},
            headers={{
                'x-superblocks-agent-key': f"{{globals()['$agentKey']}}"
            }}
        )
        if response.status_code != 200:
            raise Exception('Internal Server Error')

        buf = io.BytesIO()
        for chunk in response.iter_content(chunk_size=128):
            buf.write(chunk)
        return buf

    if '$flagWorker' in globals() and globals()['$flagWorker'] == True:
        return serialize(fetchFromController(path), name, mode)
    with open(path, "rb") as f:
        return serialize(f, name, mode)

for key, value in globals()['$superblocksFiles'].__dict__.items():
    paths = key.split('.')
    obj = globals()[paths[0]].__dict__
    for path in paths[1:]:
        if path.isdigit():
            path = int(path)
        obj = obj[path]
    # Use a partial so that key and value don't change after each iteration
    obj['readContents'] = partial(superblocksReader, key, value)

def wrapper():
"""
errorOffset = len(sharedCode.splitlines())


def convert_to_json_by_type(result):
    # Use simplejson dumps with ignore_nan enabled to convert np.nan to null

    # type detection and convertion for plotly
    if isinstance(result, PlotlyFigure):
        return result.to_json()
    return sjson.dumps(result, ignore_nan=True)


def main():
    try:
        dataIn = sys.stdin.readline()

        # Convert dict to obj so we can use . notation
        jsonData = json.loads(dataIn, object_hook=lambda d: SuperblocksObject(d))

        meta = jsonData.meta
        context = jsonData.context
        code = jsonData.code

        globalVars = {**getVars(context.globals), **getVars(context.outputs)}

        # TODO: Wrap the user's code in a library that handles the FileReader abstraction

        # Surround the data with a tag so we can separate logs from data when output is buffered
        sys.stdout.write(
            meta.dataTag
            + convert_to_json_by_type(runCode(code, globalVars))
            + meta.dataTag
        )

    except Exception as e:
        errString = str(e)
        # exc_info returns a tuple with None or a Traceback as the third item
        exc_traceback = sys.exc_info()[2]
        tb = traceback.extract_tb(exc_traceback)
        line = None
        for t in tb:
            # If the traceback includes a file called "string", this is the
            # Python code from the action configuration that is passed into
            # exec.
            if t.filename == "<string>":
                # The first line is the wrapper() function we use
                line = t.lineno - errorOffset
                break

        # If there's an error and we still haven't found a line number, it's an
        # exception when running `exec` itself (e.g. a syntax error in the
        # provided code).
        if line is None:
            # Search for "(<string>, line XX)"" where XX is the error line number,
            # remove the suffix and replace the line number with the one adjusted
            # with the offset.
            try:
                match = re.search("\(<string>, line (\d+)\)", errString)
                lineNoString = match.group(1)
                line = int(lineNoString) - errorOffset
                errString = errString.replace(match.group(), "")
            except Exception as parsingError:
                sys.stderr.write(
                    f"Unable to parse error line number {str(parsingError)}\n"
                )
                pass

        if line is not None:
            sys.stderr.write(f"Error on line {line}: {errString} ")
        else:
            sys.stderr.write(f"Error: {errString} ")


def runCode(code, context):
    moduleName = "superblocks_module"
    mySpec = importlib.util.spec_from_loader(moduleName, loader=None)
    myModule = importlib.util.module_from_spec(mySpec)
    # Copy the context variables into the scope
    # TODO: Modify the __builtins__ to restrict calling open(), exec(), eval()
    for k in context.keys():
        myModule.__dict__[k] = context[k]

    indentedCode = indent(code, "    ")
    codeStr = f"{sharedCode}{indentedCode}"
    exec(codeStr, myModule.__dict__)
    return myModule.wrapper()


def getVars(context):
    output = {}
    for p in dir(context):
        if p.startswith("__"):
            continue
        attr = getattr(context, p)
        if callable(attr):
            continue

        output[p] = attr
    return output


if __name__ == "__main__":
    main()
