using System.Text;

namespace src
{
    public class transpiler
    {
        public string transpileToC(List<token> tokens)
        {
            if (tokens.Count < 1) log.error(103);
            if (!tokens.Contains(new token { type = tokenType.outKeyword, value = "out:" })) log.error(102);

            var sb = new StringBuilder();
            var idMap = new Dictionary<string, byte>();
            sb.AppendLine("#include <stdio.h>");
            sb.AppendLine("#include <stdlib.h>");
            sb.AppendLine();

            int pc = 0;
            byte nextId = 2; // next usable register to store values in
            while (pc < tokens.Count)
            {
                if (nextId >= 64) log.error(201);
                switch (tokens[pc].type)
                {
                    case tokenType.inKeyword:
                        idMap.Clear();
                        idMap["0"] = 0;
                        idMap["1"] = 1;

                        sb.AppendLine("int main(int argc, char* argv[]){");

                        pc++;
                        byte argc = 0;
                        int start = pc;

                        while (pc < tokens.Count && tokens[pc].type != tokenType.assign)
                        {
                            if (pc + 1 < tokens.Count && tokens[pc + 1].type == tokenType.assign)
                                break;

                            idMap.Add(tokens[pc].value, nextId++);
                            argc++;
                            pc++;
                        }

                        if (argc == 0) log.warn(402);

                        sb.AppendLine($"if (argc < {argc + 1}){{ printf(\"error [1b100]: not enough inputs\\n\"); return 1; }}");
                        sb.AppendLine("register unsigned long a, b, res;");
                        sb.AppendLine("register unsigned long ram = 1UL << 1;");

                        for (int i = 0; i < argc; i++)
                            sb.AppendLine($"if (argv[{i + 1}][0] == '1') ram |= (1UL << {idMap[tokens[start + i].value]});");
                        break;

                    case tokenType.assign:
                        string dest = tokens[pc - 1].value;

                        if (!idMap.ContainsKey(dest))
                        {
                            idMap.Add(dest, nextId);
                            nextId++;
                        }

                        switch (tokens[pc + 1].type)
                        {
                            case tokenType.oneLiteral:
                                sb.AppendLine($"ram |= (1UL << {idMap[dest]});");
                                pc++;
                                break;

                            case tokenType.zeroLiteral:
                                sb.Append($"ram &= ~(1UL << {idMap[dest]});");
                                pc++;
                                break;

                            default:
                                if (tokens[pc + 2].type == tokenType.not) // separated because not is a unary operator
                                {
                                    string targetOp = tokens[pc + 1].value;
                                    byte value;

                                    if (!idMap.TryGetValue(targetOp, out value)) log.error(202);

                                    sb.AppendLine($"a = (ram >> {idMap[targetOp]}) & 1UL;");
                                    sb.AppendLine($"res = ~a & 1UL;"); 
                                    sb.AppendLine($"ram = (ram & ~(1UL << {idMap[dest]})) | (res << {idMap[dest]});");
                                    sb.AppendLine();

                                    pc += 2;
                                }
                                else
                                {
                                    string leftOp = tokens[pc + 1].value;
                                    string rightOp = tokens[pc + 3].value;
                                    byte value;
                                    switch (tokens[pc + 2].type)
                                    {
                                        case tokenType.nand:


                                            if (!idMap.TryGetValue(leftOp, out value) ||
                                                !idMap.TryGetValue(rightOp, out value)) log.error(202);

                                            sb.AppendLine($"a = (ram >> {idMap[leftOp]}) & 1UL;");
                                            sb.AppendLine($"b = (ram >> {idMap[rightOp]}) & 1UL;");
                                            sb.AppendLine("res = !(a & b) & 1UL;");
                                            sb.AppendLine(
                                                $"ram = (ram & ~(1UL << {idMap[dest]})) | (res << {idMap[dest]});");
                                            sb.AppendLine();

                                            pc += 3;
                                            break;

                                        case tokenType.and:

                                            if (!idMap.TryGetValue(leftOp, out value) ||
                                                !idMap.TryGetValue(rightOp, out value)) log.error(202);

                                            sb.AppendLine($"a = (ram >> {idMap[leftOp]}) & 1UL;");
                                            sb.AppendLine($"b = (ram >> {idMap[rightOp]}) & 1UL;");
                                            sb.AppendLine("res = (a & b) & 1UL;");
                                            sb.AppendLine(
                                                $"ram = (ram & ~(1UL << {idMap[dest]})) | (res << {idMap[dest]});");
                                            sb.AppendLine();

                                            pc += 3;
                                            break;

                                        case tokenType.or:

                                            if (!idMap.TryGetValue(leftOp, out value) ||
                                                !idMap.TryGetValue(rightOp, out value)) log.error(202);

                                            sb.AppendLine($"a = (ram >> {idMap[leftOp]}) & 1UL;");
                                            sb.AppendLine($"b = (ram >> {idMap[rightOp]}) & 1UL;");
                                            sb.AppendLine("res = (a | b) & 1UL;");
                                            sb.AppendLine(
                                                $"ram = (ram & ~(1UL << {idMap[dest]})) | (res << {idMap[dest]});");
                                            sb.AppendLine();

                                            pc += 3;
                                            break;

                                        case tokenType.nor:

                                            if (!idMap.TryGetValue(leftOp, out value) ||
                                                !idMap.TryGetValue(rightOp, out value)) log.error(202);

                                            sb.AppendLine($"a = (ram >> {idMap[leftOp]}) & 1UL;");
                                            sb.AppendLine($"b = (ram >> {idMap[rightOp]}) & 1UL;");
                                            sb.AppendLine("res = ~(a | b) & 1UL;");
                                            sb.AppendLine(
                                                $"ram = (ram & ~(1UL << {idMap[dest]})) | (res << {idMap[dest]});");
                                            sb.AppendLine();

                                            pc += 3;
                                            break;

                                        case tokenType.xor:

                                            if (!idMap.TryGetValue(leftOp, out value) ||
                                                !idMap.TryGetValue(rightOp, out value)) log.error(202);

                                            sb.AppendLine($"a = (ram >> {idMap[leftOp]}) & 1UL;");
                                            sb.AppendLine($"b = (ram >> {idMap[rightOp]}) & 1UL;");
                                            sb.AppendLine("res = (a ^ b) & 1UL;");
                                            sb.AppendLine(
                                                $"ram = (ram & ~(1UL << {idMap[dest]})) | (res << {idMap[dest]});");
                                            sb.AppendLine();

                                            pc += 3;
                                            break;

                                        case tokenType.xnor:

                                            if (!idMap.TryGetValue(leftOp, out value) ||
                                                !idMap.TryGetValue(rightOp, out value)) log.error(202);

                                            sb.AppendLine($"a = (ram >> {idMap[leftOp]}) & 1UL;");
                                            sb.AppendLine($"b = (ram >> {idMap[rightOp]}) & 1UL;");
                                            sb.AppendLine("res = ~(a ^ b) & 1UL;");
                                            sb.AppendLine(
                                                $"ram = (ram & ~(1UL << {idMap[dest]})) | (res << {idMap[dest]});");
                                            sb.AppendLine();

                                            pc += 3;
                                            break;
                                        
                                        default: // direct assignment e.g. x = y
                                            string source = tokens[pc + 1].value;

                                            sb.AppendLine($"res = (ram >> {idMap[source]}) & 1UL;");
                                            sb.AppendLine(
                                                $"ram = (ram & ~(1UL << {idMap[dest]})) | (res << {idMap[dest]});");
                                            sb.AppendLine();

                                            pc += 2;
                                            break;
                                    }
                                }

                                break;
                        }
                        break;

                    case tokenType.outKeyword:
                        pc++;
                        sb.AppendLine();
                        sb.Append("printf(\"output: ");

                        if (tokens.Count - pc == 0) log.warn(403);

                        for (int i = pc; i < tokens.Count; i++)
                            sb.Append("%lu ");
                        sb.Append("\\n\"");

                        for (int i = pc; i < tokens.Count; i++)
                        {
                            byte reg = idMap[tokens[i].value];
                            sb.Append($", (ram >> {reg}) & 1UL");
                        }
                        sb.Append(");");

                        pc = tokens.Count;
                        break;
                }
                pc++;
            }
            sb.AppendLine();
            sb.AppendLine("return 0;");
            sb.AppendLine("}");

            return sb.ToString();
        }
    }
}