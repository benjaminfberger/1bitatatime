using System.Diagnostics;
using System.Runtime.InteropServices;

namespace src
{
    internal class program
    {
        static void Main(string[] args)
        {
            if (args.Length < 1)
                log.error(1);

            string sourceFile = args[0];

            if (sourceFile.Split('.')[1] != ".1bit")
                log.warn(401);

            string outBinary = sourceFile.Split('.')[0];

            if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
                outBinary += ".exe";

            outBinary = Path.Combine(AppContext.BaseDirectory, outBinary);

            string source = File.ReadAllText(sourceFile);
            var lexer = new lexer(source);
            var transpiler = new transpiler();

            var tokens = lexer.lex();
            string c = transpiler.transpileToC(tokens);

            var startInfo = new ProcessStartInfo
            {
                FileName = "gcc",
                Arguments = $"-O3 -x c - -o \"{outBinary}\"",
                RedirectStandardInput = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            using (Process compiler = new Process { StartInfo = startInfo })
            {
                try
                {
                    compiler.Start();

                    using (StreamWriter writer = compiler.StandardInput)
                        if (writer.BaseStream.CanWrite)
                            writer.Write(c);

                    compiler.WaitForExit();

                    switch (compiler.ExitCode)
                    {
                        case 0:
                            log.success($"compiled binary: {outBinary}");
                            break;
                        default:
                            log.error(3);
                            break;
                    }
                }
                catch (System.ComponentModel.Win32Exception)
                {
                    log.error(2);
                }
            }
        }
    }
}
