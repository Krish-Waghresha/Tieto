namespace HarborOrders;

public static class Shipping
{
    public static decimal Quote(Order order, object provider)
    {
        return 4.50m;
    }
}