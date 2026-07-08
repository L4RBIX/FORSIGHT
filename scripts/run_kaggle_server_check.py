from foresight.perception.locateanything_client import LocateAnythingClient

if __name__ == "__main__":
    client = LocateAnythingClient()
    print({"health": client.health(), "base_url": client.base_url})
