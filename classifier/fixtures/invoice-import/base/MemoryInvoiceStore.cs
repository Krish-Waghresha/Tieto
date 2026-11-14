using System;
using System.Collections.Generic;
using System.Linq;

namespace InvoiceImport;

public sealed class MemoryInvoiceStore : IInvoiceStore
{
    private readonly Dictionary<Guid, Invoice> invoices = new Dictionary<Guid, Invoice>();

    public int FailBeforeCommit { get; set; }
    public int FailAfterCommit { get; set; }
    public bool RejectWrites { get; set; }
    public int SaveCalls { get; private set; }

    public Invoice Find(string tenant, string supplier, string number)
    {
        return invoices.Values.FirstOrDefault(invoice =>
            invoice.Tenant == tenant &&
            invoice.Supplier == supplier &&
            invoice.Number == number);
    }

    public void Save(Invoice invoice)
    {
        SaveCalls++;
        if (RejectWrites)
        {
            throw new InvalidOperationException("The store is read-only.");
        }

        if (FailBeforeCommit > 0)
        {
            FailBeforeCommit--;
            throw new TransientStoreException("Connection failed before commit.");
        }

        invoices[invoice.Id] = invoice;

        if (FailAfterCommit > 0)
        {
            FailAfterCommit--;
            throw new TransientStoreException("Commit succeeded but acknowledgement was lost.");
        }
    }

    public IReadOnlyList<Invoice> ForTenant(string tenant)
    {
        return invoices.Values
            .Where(invoice => invoice.Tenant == tenant)
            .OrderBy(invoice => invoice.Number, StringComparer.Ordinal)
            .ToArray();
    }

    public void Seed(Invoice invoice)
    {
        invoices.Add(invoice.Id, invoice);
    }
}