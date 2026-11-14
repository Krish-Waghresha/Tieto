using System;
using System.Collections.Generic;

namespace InvoiceImport;

public enum InvoiceStatus
{
    Active,
    Cancelled
}

public sealed record Invoice(
    Guid Id,
    string Tenant,
    string Supplier,
    string Number,
    DateOnly Date,
    string Currency,
    decimal Net,
    decimal Tax,
    InvoiceStatus Status);

public sealed record RowIssue(int Line, string Field, string Code, string Message);

public sealed record RawInvoiceRow(
    int Line,
    string Supplier,
    string Number,
    string Date,
    string Currency,
    string Net,
    string Tax);

public sealed record NormalizedInvoice(
    int Line,
    string Supplier,
    string Number,
    DateOnly Date,
    string Currency,
    decimal Net,
    decimal? Tax);

public sealed record CsvDocument(
    IReadOnlyList<RawInvoiceRow> Rows,
    IReadOnlyList<RowIssue> Issues,
    bool HeaderValid);

public sealed record NormalizationResult(
    NormalizedInvoice Value,
    IReadOnlyList<RowIssue> Issues);

public sealed record RowOutcome(
    int Line,
    string State,
    Guid? InvoiceId,
    string Currency,
    decimal Net,
    decimal Tax,
    IReadOnlyList<RowIssue> Issues);

public sealed record CurrencyTotal(string Currency, decimal Net, decimal Tax, decimal Gross);

public sealed record BatchReport(
    string Tenant,
    string State,
    int TotalRows,
    int Accepted,
    int Rejected,
    IReadOnlyList<RowOutcome> Rows,
    IReadOnlyList<CurrencyTotal> Totals,
    IReadOnlyList<RowIssue> FileIssues);

public sealed record WriteResult(bool Succeeded, Guid? Id, int Attempts, string Error);

public sealed record PreviewRow(
    int Line,
    string Supplier,
    string Number,
    string Currency,
    decimal Net,
    decimal? Tax,
    bool CanImport,
    IReadOnlyList<RowIssue> Issues);

public sealed record ImportPreviewResult(
    string Tenant,
    IReadOnlyList<PreviewRow> Rows,
    IReadOnlyList<RowIssue> FileIssues,
    int Ready,
    int NeedsAttention);

public interface IInvoiceStore
{
    Invoice Find(string tenant, string supplier, string number);
    void Save(Invoice invoice);
    IReadOnlyList<Invoice> ForTenant(string tenant);
}

public sealed class TransientStoreException : Exception
{
    public TransientStoreException(string message) : base(message)
    {
    }
}