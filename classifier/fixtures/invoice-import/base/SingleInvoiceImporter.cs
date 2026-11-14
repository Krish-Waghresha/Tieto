using System;

namespace InvoiceImport;

public sealed class SingleInvoiceImporter
{
    private readonly IInvoiceStore store;

    public SingleInvoiceImporter(IInvoiceStore store)
    {
        this.store = store;
    }

    public Guid Import(Invoice invoice)
    {
        if (string.IsNullOrWhiteSpace(invoice.Tenant))
        {
            throw new ArgumentException("Tenant is required.");
        }

        if (store.Find(invoice.Tenant, invoice.Supplier, invoice.Number) != null)
        {
            throw new InvalidOperationException("Invoice already exists.");
        }

        store.Save(invoice);
        return invoice.Id;
    }
}