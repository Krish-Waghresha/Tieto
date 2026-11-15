using System;
using System.Collections.Generic;

namespace InvoiceImport;

public sealed class DuplicatePolicy
{
    private readonly IInvoiceStore store;

    public DuplicatePolicy(IInvoiceStore store)
    {
        this.store = store;
    }

    public RowIssue Check(string tenant, NormalizedInvoice invoice, ISet<string> seen)
    {
        string key = MakeKey(tenant, invoice.Supplier, invoice.Number);
        if (seen.Contains(key))
        {
            return new RowIssue(invoice.Line, "number", "duplicate-in-batch", "This invoice appeared earlier in the batch.");
        }

        Invoice existing = store.Find(tenant, invoice.Supplier, invoice.Number);
        if (existing != null)
        {
            string code = existing.Status == InvoiceStatus.Cancelled
                ? "cancelled-invoice-exists"
                : "duplicate-existing";
            return new RowIssue(invoice.Line, "number", code, "An invoice with this identity already exists.");
        }

        return null;
    }

    public void Remember(string tenant, NormalizedInvoice invoice, ISet<string> seen)
    {
        seen.Add(MakeKey(tenant, invoice.Supplier, invoice.Number));
    }

    public static ISet<string> NewBatch()
    {
        return new HashSet<string>(StringComparer.Ordinal);
    }

    private static string MakeKey(string tenant, string supplier, string number)
    {
        return string.Join("\u001f", tenant, supplier, number);
    }
}