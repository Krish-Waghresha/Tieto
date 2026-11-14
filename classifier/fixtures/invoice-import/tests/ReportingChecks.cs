using System;
using System.Linq;
using System.Text.Json;

namespace InvoiceImport.Tests;

public static class ReportingChecks
{
    private static readonly string[] Reconciler = { "BatchReconciler.cs" };
    private static readonly string[] Writer = { "ReportWriter.cs" };

    public static void Run()
    {
        Checks.Run("report.empty", "INV-106", Reconciler, () =>
        {
            BatchReport report = BatchReconciler.Build("tenant-a", Array.Empty<RowOutcome>(), Array.Empty<RowIssue>());
            Checks.Equal("completed", report.State);
            Checks.Equal(0, report.TotalRows);
            Checks.Equal(0, report.Totals.Count);
        });

        Checks.Run("report.reconciles-mixed-rows", "INV-106", Reconciler, () =>
        {
            RowOutcome good = BatchReconciler.Accept(Samples.Normalized(2), 20m, Guid.NewGuid());
            RowOutcome bad = BatchReconciler.Reject(3, new[] { new RowIssue(3, "net", "range", "Invalid amount.") });
            BatchReport report = BatchReconciler.Build("tenant-a", new[] { bad, good }, Array.Empty<RowIssue>());
            Checks.Equal("partial-success", report.State);
            Checks.Equal(2, report.TotalRows);
            Checks.Equal(report.TotalRows, report.Accepted + report.Rejected);
            Checks.Equal(2, report.Rows[0].Line);
            Checks.Equal(100m, report.Totals.Single().Net);
            Checks.Equal(120m, report.Totals.Single().Gross);
        });

        Checks.Run("report.currency-separation", "INV-106", Reconciler, () =>
        {
            var euro = Samples.Normalized(2);
            var dollar = Samples.Normalized(3) with { Currency = "USD", Net = 200m };
            BatchReport report = BatchReconciler.Build("tenant-a", new[]
            {
                BatchReconciler.Accept(dollar, 40m, Guid.NewGuid()),
                BatchReconciler.Accept(euro, 20m, Guid.NewGuid())
            }, Array.Empty<RowIssue>());
            Checks.Equal(2, report.Totals.Count);
            Checks.Equal("EUR", report.Totals[0].Currency);
            Checks.Equal(120m, report.Totals[0].Gross);
            Checks.Equal(240m, report.Totals[1].Gross);
        });

        Checks.Run("report.all-rejected", "INV-106", Reconciler, () =>
        {
            RowOutcome row = BatchReconciler.Reject(2, new[] { new RowIssue(2, "row", "bad", "Invalid row.") });
            BatchReport report = BatchReconciler.Build("tenant-a", new[] { row }, Array.Empty<RowIssue>());
            Checks.Equal("rejected", report.State);
            Checks.Equal(0, report.Accepted);
            Checks.Equal(1, report.Rejected);
            Checks.Equal(0, report.Totals.Count);
        });

        Checks.Run("report.file-rejection", "INV-106", Reconciler, () =>
        {
            var issue = new RowIssue(1, "file", "bad", "Invalid file.");
            BatchReport report = BatchReconciler.Build("tenant-a", Array.Empty<RowOutcome>(), new[] { issue });
            Checks.Equal("file-rejected", report.State);
            Checks.Equal(1, report.FileIssues.Count);
        });

        Checks.Run("report.duplicate-source-line", "INV-106", Reconciler, () =>
        {
            RowOutcome row = BatchReconciler.Accept(Samples.Normalized(), 20m, Guid.NewGuid());
            Checks.Throws<ArgumentException>(() => BatchReconciler.Build("tenant-a", new[] { row, row }, Array.Empty<RowIssue>()));
        });

        Checks.Run("report.rejected-cannot-contribute", "INV-106", Reconciler, () =>
        {
            var issue = new RowIssue(2, "row", "bad", "Rejected.");
            var row = new RowOutcome(2, "rejected", null, "EUR", 100m, 20m, new[] { issue });
            Checks.Throws<ArgumentException>(() => BatchReconciler.Build("tenant-a", new[] { row }, Array.Empty<RowIssue>()));
            Checks.Throws<ArgumentException>(() => BatchReconciler.Reject(2, Array.Empty<RowIssue>()));
        });

        Checks.Run("report.accepted-needs-identity", "INV-106", Reconciler, () =>
        {
            var row = new RowOutcome(2, "accepted", null, "EUR", 100m, 20m, Array.Empty<RowIssue>());
            Checks.Throws<ArgumentException>(() => BatchReconciler.Build("tenant-a", new[] { row }, Array.Empty<RowIssue>()));
        });

        Checks.Run("report.unknown-state", "INV-106", Reconciler, () =>
        {
            var row = new RowOutcome(2, "pending", null, "EUR", 0m, 0m, Array.Empty<RowIssue>());
            Checks.Throws<ArgumentException>(() => BatchReconciler.Build("tenant-a", new[] { row }, Array.Empty<RowIssue>()));
        });

        Checks.Run("json.round-trip", "INV-106", Writer, () =>
        {
            RowOutcome row = BatchReconciler.Accept(Samples.Normalized(), 20m, Guid.NewGuid());
            BatchReport report = BatchReconciler.Build("tenant-a", new[] { row }, Array.Empty<RowIssue>());
            using var json = JsonDocument.Parse(ReportWriter.Write(report));
            Checks.Equal("tenant-a", json.RootElement.GetProperty("tenant").GetString());
            Checks.Equal(1, json.RootElement.GetProperty("accepted").GetInt32());
            Checks.Equal(120m, json.RootElement.GetProperty("totals")[0].GetProperty("gross").GetDecimal());
            Checks.Equal(row.InvoiceId.Value, json.RootElement.GetProperty("rows")[0].GetProperty("invoiceId").GetGuid());
        });

        Checks.Run("json.escape-and-minimize", "INV-106", Writer, () =>
        {
            string message = "Quoted \"value\"\n<script>not code</script>";
            RowOutcome row = BatchReconciler.Reject(2, new[] { new RowIssue(2, "row", "bad", message) });
            BatchReport report = BatchReconciler.Build("tenant-a", new[] { row }, Array.Empty<RowIssue>());
            string output = ReportWriter.Write(report);
            using var json = JsonDocument.Parse(output);
            var item = json.RootElement.GetProperty("rows")[0];
            Checks.Equal(message, item.GetProperty("issues")[0].GetProperty("message").GetString());
            Checks.Equal(JsonValueKind.Null, item.GetProperty("invoiceId").ValueKind);
            Checks.Equal(false, item.TryGetProperty("supplier", out var ignored));
            Checks.Equal(false, item.TryGetProperty("net", out ignored));
            Checks.Equal(false, output.Contains("<script>"));
        });

        Checks.Run("json.file-issues", "INV-106", Writer, () =>
        {
            var issue = new RowIssue(1, "header", "missing", "Header required.");
            var report = BatchReconciler.Build("tenant-a", Array.Empty<RowOutcome>(), new[] { issue });
            using var json = JsonDocument.Parse(ReportWriter.Write(report));
            Checks.Equal("missing", json.RootElement.GetProperty("fileIssues")[0].GetProperty("code").GetString());
        });
    }
}