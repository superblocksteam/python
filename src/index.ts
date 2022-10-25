import { parser } from '@lezer/python';
import {
  EvaluationPair,
  ExecutionOutput,
  extractPythonEvaluationPairs,
  IntegrationError,
  PythonDatasourceConfiguration,
  PythonParser
} from '@superblocksteam/shared';
import {
  getTreePathToDiskPath,
  LanguagePlugin,
  PluginExecutionProps,
  ProcessInput,
  RequestFile,
  spawnStdioProcess
} from '@superblocksteam/shared-backend';

export default class PythonPlugin extends LanguagePlugin {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async evaluateBindingPairs(code: string, entitiesToExtract: Set<string>, dataContext: Record<string, any>): Promise<EvaluationPair[]> {
    return extractPythonEvaluationPairs(code, entitiesToExtract, dataContext, (parser as unknown) as PythonParser);
  }

  async execute({
    context,
    datasourceConfiguration,
    actionConfiguration,
    files
  }: PluginExecutionProps<PythonDatasourceConfiguration>): Promise<ExecutionOutput> {
    try {
      const timeout = Number(this.pluginConfiguration.pythonExecutionTimeoutMs);
      const output = await this.runPython({ context: context, code: actionConfiguration.body ?? '', files }, timeout);
      return output;
    } catch (err) {
      throw new IntegrationError(err);
    }
  }

  async runPython(input: ProcessInput, timeout: number): Promise<ExecutionOutput> {
    const filePaths = getTreePathToDiskPath(input.context.globals, input.files as Array<RequestFile>);
    input.context.addGlobalVariableOverride('$superblocksFiles', filePaths);
    return spawnStdioProcess(`python3`, ['-u', `${__dirname}/run.py`], input, timeout);
  }
}
