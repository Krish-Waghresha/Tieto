using System;
using System.Linq;
using System.Threading;

namespace InvoiceImport.Tests;

public sealed class FixedTaxProvider
{
    public decimal Rate { get; set; } = 0.20m;
    public int Calls { get; private set; }

    public decimal RateFor(string currency, DateOnly date)
    {
        Calls++;
        return Rate;
    }
}

public static class WorkflowChecks
{
    public static void Run()
    {
        Checks.Run("batch.partial-success", "INV-109", new[] { "BatchImporter.cs" }, () =>
        {
            var store = new MemoryInvoiceStore();
            string csv = Samples.Header + Samples.Row("GOOD-1") + Samples.Row("BAD", "invalid") + Samples.Row("GOOD-2");
            BatchReport report = new BatchImporter(store).Import("tenant-a", csv, Samples.Today, null, CancellationToken.None);
            Checks.Equal(2, report.Accepted);
            Checks.Equal(1, report.Rejected);
            Checks.Equal(3, report.TotalRows);
            Checks.Equal(2, store.ForTenant("tenant-a").Count);
            Checks.Equal(240m, report.Totals.Single().Gross);
        });

        Checks.Run("batch.csv-error-isolation", "INV-109", new[] { "BatchImporter.cs" }, () =>
        {
            var store = new MemoryInvoiceStore();
            string csv = Samples.Header + "broken,row\n" + Samples.Row();
            var report = new BatchImporter(store).Import("tenant-a", csv, Samples.Today, null, CancellationToken.None);
            Checks.Equal(1, report.Accepted);
            Checks.Equal(1, report.Rejected);
            Checks.Equal(2, report.Rows[0].Line);
            Checks.Equal(3, report.Rows[1].Line);
        });

        Checks.Run("batch.tenant-isolation", "INV-109", new[] { "BatchImporter.cs" }, () =>
        {
            var store = new MemoryInvoiceStore();
            store.Seed(Samples.Existing("tenant-b"));
            var report = new BatchImporter(store).Import("tenant-a", Samples.Header + Samples.Row(), Samples.Today, null, CancellationToken.None);
            Checks.Equal(1, report.Accepted);
            Checks.Equal(1, store.ForTenant("tenant-a").Count);
            Checks.Equal(1, store.ForTenant("tenant-b").Count);
        });

        Checks.Run("batch.invalid-tenant", "INV-109", new[] { "BatchImporter.cs" }, () =>
        {
            var importer = new BatchImporter(new MemoryInvoiceStore());
            Checks.Throws<ArgumentException>(() => importer.Import(" ", Samples.Header, Samples.Today, null, CancellationToken.None));
            Checks.Throws<ArgumentException>(() => BatchImporter.RequireTenant("bad\ntenant"));
        });

        Checks.Run("batch.cancel-before-write", "INV-109", new[] { "BatchImporter.cs" }, () =>
        {
            var store = new MemoryInvoiceStore();
            var cancellation = new CancellationToken(true);
            Checks.Throws<OperationCanceledException>(() => new BatchImporter(store).Import("tenant-a", Samples.Header + Samples.Row(), Samples.Today, null, cancellation));
            Checks.Equal(0, store.SaveCalls);
        });

        Checks.Run("batch.invalid-file-no-writes", "INV-109", new[] { "BatchImporter.cs" }, () =>
        {
            var store = new MemoryInvoiceStore();
            var report = new BatchImporter(store).Import("tenant-a", "invalid header\n", Samples.Today, null, CancellationToken.None);
            Checks.Equal("file-rejected", report.State);
            Checks.Equal(0, store.SaveCalls);
        });

        Checks.Run("batch.provider-missing", "INV-109", new[] { "BatchImporter.cs" }, () =>
        {
            var store = new MemoryInvoiceStore();
            var report = new BatchImporter(store).Import("tenant-a", Samples.Header + Samples.Row(tax: ""), Samples.Today, null, CancellationToken.None);
            Checks.Equal(0, report.Accepted);
            Checks.Equal(1, report.Rejected);
            Checks.Equal(0, store.SaveCalls);
        });

        Checks.Run("batch.store-failure-reported", "INV-109", new[] { "BatchImporter.cs" }, () =>
        {
            var store = new MemoryInvoiceStore { RejectWrites = true };
            var report = new BatchImporter(store).Import("tenant-a", Samples.Header + Samples.Row(), Samples.Today, null, CancellationToken.None);
            Checks.Equal(1, report.Rejected);
            Checks.Equal(0, report.Totals.Count);
        });

        Checks.Run("duplicate.active", "INV-104", new[] { "DuplicatePolicy.cs" }, () =>
        {
            var store = new MemoryInvoiceStore();
            store.Seed(Samples.Existing());
            var policy = new DuplicatePolicy(store);
            Checks.Equal("duplicate-existing", policy.Check("tenant-a", Samples.Normalized(), DuplicatePolicy.NewBatch()).Code);
        });

        Checks.Run("duplicate.cancelled-observation", "INV-104", new[] { "DuplicatePolicy.cs" }, () =>
        {
            var store = new MemoryInvoiceStore();
            store.Seed(Samples.Existing(status: InvoiceStatus.Cancelled));
            var policy = new DuplicatePolicy(store);
            Checks.Equal("cancelled-invoice-exists", policy.Check("tenant-a", Samples.Normalized(), DuplicatePolicy.NewBatch()).Code);
        });

        Checks.Run("duplicate.tenant-boundary", "INV-104", new[] { "DuplicatePolicy.cs" }, () =>
        {
            var store = new MemoryInvoiceStore();
            store.Seed(Samples.Existing("tenant-b"));
            Checks.Equal(null, new DuplicatePolicy(store).Check("tenant-a", Samples.Normalized(), DuplicatePolicy.NewBatch()));
        });

        Checks.Run("duplicate.batch-memory", "INV-104", new[] { "DuplicatePolicy.cs" }, () =>
        {
            var policy = new DuplicatePolicy(new MemoryInvoiceStore());
            var seen = DuplicatePolicy.NewBatch();
            policy.Remember("tenant-a", Samples.Normalized(), seen);
            Checks.Equal("duplicate-in-batch", policy.Check("tenant-a", Samples.Normalized(), seen).Code);
        });

        Checks.Run("retry.before-commit", "INV-105", new[] { "RetryingInvoiceWriter.cs" }, () =>
        {
            var store = new MemoryInvoiceStore { FailBeforeCommit = 1 };
            var result = new RetryingInvoiceWriter(store, 3).Write("tenant-a", Samples.Normalized(), 20m);
            Checks.Equal(true, result.Succeeded);
            Checks.Equal(2, result.Attempts);
            Checks.Equal(1, store.ForTenant("tenant-a").Count);
        });

        Checks.Run("retry.bounded", "INV-105", new[] { "RetryingInvoiceWriter.cs" }, () =>
        {
            var store = new MemoryInvoiceStore { FailBeforeCommit = 10 };
            var result = new RetryingInvoiceWriter(store, 3).Write("tenant-a", Samples.Normalized(), 20m);
            Checks.Equal(false, result.Succeeded);
            Checks.Equal(3, store.SaveCalls);
            Checks.Equal(0, store.ForTenant("tenant-a").Count);
        });

        Checks.Run("retry.permanent-not-retried", "INV-105", new[] { "RetryingInvoiceWriter.cs" }, () =>
        {
            var store = new MemoryInvoiceStore { RejectWrites = true };
            Checks.Equal(false, new RetryingInvoiceWriter(store, 3).Write("tenant-a", Samples.Normalized(), 20m).Succeeded);
            Checks.Equal(1, store.SaveCalls);
        });

        Checks.Run("retry.attempt-config", "INV-105", new[] { "RetryingInvoiceWriter.cs" }, () =>
        {
            Checks.Throws<ArgumentOutOfRangeException>(() => new RetryingInvoiceWriter(new MemoryInvoiceStore(), 0));
            Checks.Throws<ArgumentOutOfRangeException>(() => new RetryingInvoiceWriter(new MemoryInvoiceStore(), 4));
        });

        Checks.Run("retry.lost-acknowledgement", "INV-105", new[] { "RetryingInvoiceWriter.cs" }, () =>
        {
            var store = new MemoryInvoiceStore { FailAfterCommit = 1 };
            var result = new RetryingInvoiceWriter(store, 3).Write("tenant-a", Samples.Normalized(), 20m);
            Checks.Equal(true, result.Succeeded);
            Checks.Equal(1, store.ForTenant("tenant-a").Count);
        });

        Checks.Run("tax.explicit-bypasses-provider", "INV-107", new[] { "TaxGateway.cs" }, () =>
        {
            Checks.Equal(20m, TaxGateway.Resolve(Samples.Normalized(), null));
        });

        Checks.Run("tax.controlled-adapter", "INV-107", new[] { "TaxGateway.cs" }, () =>
        {
            var provider = new FixedTaxProvider();
            Checks.Equal(20m, TaxGateway.Resolve(Samples.Normalized(tax: null), provider));
            Checks.Equal(1, provider.Calls);
        });

        Checks.Run("tax.invalid-rate", "INV-107", new[] { "TaxGateway.cs" }, () =>
        {
            Checks.Throws<InvalidOperationException>(() => TaxGateway.Resolve(Samples.Normalized(tax: null), new FixedTaxProvider { Rate = -1m }));
            Checks.Throws<InvalidOperationException>(() => TaxGateway.Resolve(Samples.Normalized(tax: null), null));
        });

        Checks.Run("preview.no-writes", "INV-108", new[] { "ImportPreview.cs" }, () =>
        {
            var store = new MemoryInvoiceStore();
            var preview = new ImportPreview(store).Create("tenant-a", Samples.Header + Samples.Row(), Samples.Today);
            Checks.Equal(1, preview.Ready);
            Checks.Equal(0, store.SaveCalls);
        });

        Checks.Run("preview.input-order-and-errors", "INV-108", new[] { "ImportPreview.cs" }, () =>
        {
            string csv = Samples.Header + Samples.Row("FIRST") + "bad,row\n" + Samples.Row("LAST", "invalid");
            var preview = new ImportPreview(new MemoryInvoiceStore()).Create("tenant-a", csv, Samples.Today);
            Checks.Equal(3, preview.Rows.Count);
            Checks.Equal(1, preview.Ready);
            Checks.Equal(2, preview.NeedsAttention);
            Checks.Equal(4, preview.Rows[2].Line);
        });

        Checks.Run("preview.missing-tax", "INV-108", new[] { "ImportPreview.cs" }, () =>
        {
            var preview = new ImportPreview(new MemoryInvoiceStore()).Create("tenant-a", Samples.Header + Samples.Row(tax: ""), Samples.Today);
            Checks.Equal(0, preview.Ready);
            Samples.HasIssue(preview.Rows.Single().Issues, "tax", "provider-needed");
        });

        Checks.Run("preview.duplicate-and-invalid-file", "INV-108", new[] { "ImportPreview.cs" }, () =>
        {
            var preview = new ImportPreview(new MemoryInvoiceStore());
            var repeated = preview.Create("tenant-a", Samples.Header + Samples.Row() + Samples.Row(), Samples.Today);
            Checks.Equal(1, repeated.Ready);
            Checks.Equal(1, repeated.NeedsAttention);
            Checks.True(preview.Create("tenant-a", "bad header\n", Samples.Today).FileIssues.Count > 0, "Invalid file must have issues.");
        });
    }
}