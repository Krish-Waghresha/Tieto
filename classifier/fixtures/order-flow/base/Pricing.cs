namespace HarborOrders;

public static class Pricing
{
    public static decimal Subtotal(Order order)
    {
        return order.UnitPrice * order.Quantity;
    }

    public static decimal Total(Order order)
    {
        decimal subtotal = Subtotal(order);
        return subtotal;
    }
}