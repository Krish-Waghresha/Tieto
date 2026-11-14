namespace HarborOrders;

public static class Shipping
{
    public static decimal Quote(Order order, object provider)
    {
        dynamic carrier = provider;
        return (decimal)carrier.PriceFor(order.Postcode);
    }
}