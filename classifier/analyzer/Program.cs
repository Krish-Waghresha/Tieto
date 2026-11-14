using System.Security.Cryptography;
using System.Text.Json;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.CodeAnalysis.FlowAnalysis;
using Microsoft.CodeAnalysis.Operations;

if (args.Length < 2 || args.Length > 3)
{
    Console.Error.WriteLine("Usage: Analyzer <base-source-directory> <head-source-directory> [protected-attribute-name]");
    return 2;
}

var framework = ((string?)AppContext.GetData("TRUSTED_PLATFORM_ASSEMBLIES") ?? "")
    .Split(Path.PathSeparator, StringSplitOptions.RemoveEmptyEntries)
    .Select(path => MetadataReference.CreateFromFile(path)).ToArray();
var protectedAttribute = args.Length == 3 ? args[2] : "ReviewBoundaryAttribute";
var before = Snapshot.Load(args[0], framework, protectedAttribute);
var after = Snapshot.Load(args[1], framework, protectedAttribute);
var nodes = new List<object>();
var changed = new HashSet<string>();

foreach (var id in before.Methods.Keys.Union(after.Methods.Keys).Order())
{
    before.Methods.TryGetValue(id, out var oldMethod);
    after.Methods.TryGetValue(id, out var newMethod);
    var change = oldMethod is null ? "added" : newMethod is null ? "removed" : oldMethod.Code != newMethod.Code ? "modified" : "unchanged";
    if (change != "unchanged") changed.Add(id);
    var current = newMethod ?? oldMethod!;
    var equivalent = oldMethod is not null && newMethod is not null && oldMethod.Tokens == newMethod.Tokens && oldMethod.Trivia == newMethod.Trivia;
    nodes.Add(new
    {
        id, kind = "method", name = current.Name, label = current.Label, file = current.File,
        change, before = oldMethod?.PublicFacts(), after = newMethod?.PublicFacts(),
        facts = new
        {
            tokensEquivalent = equivalent,
            signaturesEquivalent = oldMethod?.Signature == newMethod?.Signature,
            semanticCallsEquivalent = oldMethod is not null && newMethod is not null && oldMethod.CallSignatures.SequenceEqual(newMethod.CallSignatures),
            protectedBefore = oldMethod?.Protected ?? false,
            protectedAfter = newMethod?.Protected ?? false,
            hasDirectives = before.HasDirectives || after.HasDirectives,
            sourceSensitive = before.SourceSensitive || after.SourceSensitive,
            compilationComplete = before.Errors.Length == 0 && after.Errors.Length == 0,
        },
    });
}

foreach (var file in before.Files.Keys.Union(after.Files.Keys).Order())
{
    before.Files.TryGetValue(file, out var oldText);
    after.Files.TryGetValue(file, out var newText);
    if (oldText == newText) continue;
    var methodsChanged = before.Methods.Values.Concat(after.Methods.Values).Any(method => method.File == file && changed.Contains(method.Id));
    if (!file.EndsWith(".cs") || !methodsChanged || Snapshot.OutsideMethodTokens(oldText) != Snapshot.OutsideMethodTokens(newText))
    {
        var id = "file:" + file;
        changed.Add(id);
        nodes.Add(new { id, kind = "file", name = file, label = file, file,
            change = oldText is null ? "added" : newText is null ? "removed" : "modified",
            before = oldText is null ? null : new { code = oldText, line = 1 },
            after = newText is null ? null : new { code = newText, line = 1 },
            reason = "Change outside the method-level analysis contract" });
    }
}

var allEdges = before.Edges.Concat(after.Edges).GroupBy(edge => (edge.Source, edge.Target)).Select(group =>
{
    var edge = group.First();
    return new
    {
        source = edge.Source, target = edge.Target, label = edge.Label, kind = edge.Kind,
        change = !before.Edges.Any(item => item.Source == edge.Source && item.Target == edge.Target) ? "added" :
            !after.Edges.Any(item => item.Source == edge.Source && item.Target == edge.Target) ? "removed" : "unchanged",
        sites = group.Select(item => new { file = item.File, line = item.Line }).Distinct().ToArray(),
    };
}).ToArray();
var visible = new HashSet<string>(changed);
foreach (var edge in allEdges)
{
    if (changed.Contains(edge.source) || changed.Contains(edge.target))
    {
        visible.Add(edge.source);
        visible.Add(edge.target);
    }
}
var unknownNodes = before.Edges.Concat(after.Edges).Where(edge => edge.Kind == "dynamic" || edge.Kind == "unresolved")
    .DistinctBy(edge => edge.Target).Where(edge => visible.Contains(edge.Target))
    .Select(edge => new { id = edge.Target, kind = "external", name = edge.Label, label = edge.Label, change = "context", reason = "Target cannot be statically resolved" });
var filteredNodes = nodes.Where(node => visible.Contains((string)node.GetType().GetProperty("id")!.GetValue(node)!)).Concat(unknownNodes.Cast<object>()).ToArray();
var output = new
{
    schemaVersion = 1,
    tool = new { name = "Microsoft.CodeAnalysis.CSharp", version = typeof(CSharpCompilation).Assembly.GetName().Version?.ToString() },
    contract = "C# 12 source-only compilation against this .NET 8 runtime; no MSBuild, source generators, custom analyzers, or program execution",
    baseHash = before.Hash, headHash = after.Hash,
    changedFiles = before.Files.Keys.Union(after.Files.Keys).Where(file => before.Files.GetValueOrDefault(file) != after.Files.GetValueOrDefault(file)).Order().ToArray(),
    errors = new { before = before.Errors, after = after.Errors },
    nodes = filteredNodes,
    edges = allEdges.Where(edge => visible.Contains(edge.source) && visible.Contains(edge.target)).ToArray(),
};
Console.WriteLine(JsonSerializer.Serialize(output, new JsonSerializerOptions { WriteIndented = true }));
return 0;

sealed record CallEdge(string Source, string Target, string Label, string Kind, string File, int Line);

sealed class MethodInfo
{
    public required string Id { get; init; }
    public required string Name { get; init; }
    public required string Label { get; init; }
    public required string File { get; init; }
    public required string Code { get; init; }
    public required string Tokens { get; init; }
    public required string Trivia { get; init; }
    public required string Signature { get; init; }
    public required bool Protected { get; init; }
    public required bool Public { get; init; }
    public required int Line { get; init; }
    public required int EndLine { get; init; }
    public required object[] Blocks { get; init; }
    public required string[] Conditions { get; init; }
    public required string[] Operators { get; init; }
    public required string[] CallSignatures { get; init; }
    public required string[] UnresolvedCalls { get; init; }
    public required object DataFlow { get; init; }
    public required bool FlowAvailable { get; init; }

    public object PublicFacts() => new
    {
        code = Code, line = Line, endLine = EndLine, signature = Signature, isPublic = Public, protectedBoundary = Protected,
        cfg = Blocks, conditions = Conditions, operators = Operators,
        callSignatures = CallSignatures, unresolvedCalls = UnresolvedCalls, dataFlow = DataFlow, flowAvailable = FlowAvailable,
    };
}

sealed class Snapshot
{
    public Dictionary<string, string> Files { get; } = new();
    public Dictionary<string, MethodInfo> Methods { get; } = new();
    public List<CallEdge> Edges { get; } = new();
    public object[] Errors { get; private set; } = [];
    public bool HasDirectives { get; private set; }
    public bool SourceSensitive { get; private set; }
    public string Hash => Convert.ToHexString(SHA256.HashData(System.Text.Encoding.UTF8.GetBytes(
        string.Join("\n", Files.OrderBy(item => item.Key).Select(item => item.Key + "\0" + item.Value))))).ToLowerInvariant();

    public static string OutsideMethodTokens(string? source)
    {
        if (source is null) return "";
        var root = CSharpSyntaxTree.ParseText(source).GetRoot();
        var spans = root.DescendantNodes().OfType<MethodDeclarationSyntax>().Select(node => node.FullSpan).ToArray();
        return string.Join("|", root.DescendantTokens().Where(token => !spans.Any(span => span.Contains(token.Span))).Select(token => token.RawKind + ":" + token.Text));
    }

    public static Snapshot Load(string directory, MetadataReference[] framework, string protectedAttribute)
    {
        var snapshot = new Snapshot();
        foreach (var path in Directory.GetFiles(directory, "*", SearchOption.AllDirectories).Order())
        {
            var relative = Path.GetRelativePath(directory, path).Replace('\\', '/');
            if (relative.Split('/').Any(part => part is ".git" or "bin" or "obj")) continue;
            snapshot.Files[relative] = File.ReadAllText(path);
        }
        var trees = snapshot.Files.Where(item => item.Key.EndsWith(".cs"))
            .Select(item => CSharpSyntaxTree.ParseText(item.Value, CSharpParseOptions.Default.WithLanguageVersion(LanguageVersion.CSharp12), item.Key)).ToArray();
        var compilation = CSharpCompilation.Create("ReviewedSnapshot", trees, framework,
            new CSharpCompilationOptions(OutputKind.DynamicallyLinkedLibrary));
        snapshot.Errors = compilation.GetDiagnostics().Where(item => item.Severity == DiagnosticSeverity.Error)
            .Select(item => (object)new { id = item.Id, message = item.GetMessage(), file = item.Location.SourceTree?.FilePath,
                line = item.Location.IsInSource ? item.Location.GetLineSpan().StartLinePosition.Line + 1 : 0 }).ToArray();
        foreach (var tree in trees)
        {
            var root = tree.GetRoot();
            var model = compilation.GetSemanticModel(tree);
            snapshot.HasDirectives |= root.DescendantTrivia(descendIntoTrivia: true).Any(trivia => trivia.IsDirective);
            snapshot.SourceSensitive |= root.DescendantNodes().OfType<AttributeSyntax>().Any(attribute =>
                model.GetSymbolInfo(attribute).Symbol is IMethodSymbol constructor && constructor.ContainingType.Name.StartsWith("Caller"));
            foreach (var method in root.DescendantNodes().OfType<MethodDeclarationSyntax>())
            {
                var symbol = model.GetDeclaredSymbol(method);
                if (symbol is null) continue;
                var id = symbol.GetDocumentationCommentId() ?? symbol.ToDisplayString();
                var calls = new List<string>();
                var unresolved = new List<string>();
                foreach (var call in method.DescendantNodes().OfType<InvocationExpressionSyntax>())
                {
                    var operation = model.GetOperation(call);
                    if (operation is INameOfOperation) continue;
                    var line = call.GetLocation().GetLineSpan().StartLinePosition.Line + 1;
                    if (operation is IInvocationOperation invocation)
                    {
                        var target = (invocation.TargetMethod.ReducedFrom ?? invocation.TargetMethod).OriginalDefinition;
                        calls.Add(target.ToDisplayString(SymbolDisplayFormat.FullyQualifiedFormat) + ":" + target.ReturnType.ToDisplayString());
                        snapshot.SourceSensitive |= target.Parameters.Any(parameter => parameter.GetAttributes().Any(attribute => attribute.AttributeClass?.Name.StartsWith("Caller") == true));
                        if (target.Locations.Any(location => location.IsInSource))
                        {
                            snapshot.Edges.Add(new(id, target.GetDocumentationCommentId() ?? target.ToDisplayString(), target.Name, "call", tree.FilePath, line));
                        }
                    }
                    else
                    {
                        var kind = operation is IDynamicInvocationOperation ? "dynamic" : "unresolved";
                        var label = call.Expression.ToString();
                        unresolved.Add(label);
                        snapshot.Edges.Add(new(id, kind + ":" + id + ":" + label, label, kind, tree.FilePath, line));
                    }
                }
                ControlFlowGraph? cfg = null;
                try { cfg = ControlFlowGraph.Create(method, model); }
                catch (ArgumentException) { }
                DataFlowAnalysis? flow = method.Body is not null ? model.AnalyzeDataFlow(method.Body) :
                    method.ExpressionBody is not null ? model.AnalyzeDataFlow(method.ExpressionBody.Expression) : null;
                var info = new MethodInfo
                {
                    Id = id, Name = symbol.ContainingType.ToDisplayString() + "." + symbol.Name,
                    Label = symbol.ContainingType.Name + "." + symbol.Name, File = tree.FilePath,
                    Code = method.ToFullString(), Line = method.GetLocation().GetLineSpan().StartLinePosition.Line + 1,
                    EndLine = method.GetLocation().GetLineSpan().EndLinePosition.Line + 1,
                    Tokens = string.Join("|", method.DescendantTokens().Select(token => token.RawKind + ":" + token.Text)),
                    Trivia = string.Join("|", method.DescendantTrivia(descendIntoTrivia: true).Where(trivia => !trivia.IsKind(SyntaxKind.WhitespaceTrivia) && !trivia.IsKind(SyntaxKind.EndOfLineTrivia)).Select(trivia => trivia.RawKind + ":" + trivia.ToFullString())),
                    Signature = symbol.DeclaredAccessibility + ":" + symbol.ReturnType.ToDisplayString(SymbolDisplayFormat.FullyQualifiedFormat) + ":" + symbol.ToDisplayString(SymbolDisplayFormat.CSharpErrorMessageFormat),
                    Protected = symbol.GetAttributes().Any(attribute => attribute.AttributeClass?.Name == protectedAttribute),
                    Public = symbol.DeclaredAccessibility == Accessibility.Public,
                    Blocks = cfg?.Blocks.Select(block => (object)new
                    {
                        id = block.Ordinal, kind = block.Kind.ToString(), reachable = block.IsReachable,
                        conditionKind = block.ConditionKind.ToString(), condition = block.BranchValue?.Syntax.ToString(),
                        operations = block.Operations.Select(operation => operation.Syntax.ToString()).ToArray(),
                        next = block.FallThroughSuccessor?.Destination?.Ordinal,
                        conditional = block.ConditionalSuccessor?.Destination?.Ordinal,
                    }).ToArray() ?? [],
                    Conditions = cfg?.Blocks.Where(block => block.ConditionKind != ControlFlowConditionKind.None).Select(block => block.BranchValue?.Syntax.ToString() ?? "").ToArray() ?? [],
                    Operators = method.DescendantNodes().OfType<BinaryExpressionSyntax>().Select(expression => expression.OperatorToken.Text).ToArray(),
                    CallSignatures = calls.Order().ToArray(), UnresolvedCalls = unresolved.ToArray(),
                    FlowAvailable = cfg is not null && flow?.Succeeded == true,
                    DataFlow = new { succeeded = flow?.Succeeded ?? false,
                        reads = flow?.ReadInside.Select(item => item.Name).Order().ToArray() ?? [],
                        writes = flow?.WrittenInside.Select(item => item.Name).Order().ToArray() ?? [],
                        flowsIn = flow?.DataFlowsIn.Select(item => item.Name).Order().ToArray() ?? [],
                        flowsOut = flow?.DataFlowsOut.Select(item => item.Name).Order().ToArray() ?? [] },
                };
                snapshot.Methods[id] = info;
            }
        }
        return snapshot;
    }
}