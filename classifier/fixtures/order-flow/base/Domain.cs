using System;

namespace HarborOrders;

[AttributeUsage(AttributeTargets.Method)]
public sealed class ReviewBoundaryAttribute : Attribute
{
}

public sealed record User(bool Active, string Tenant);
public sealed record Order(string Id, string Tenant, decimal UnitPrice, int Quantity, string Postcode);