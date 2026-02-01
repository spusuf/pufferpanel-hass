import asyncio
import aiohttp
import sys
import logging
_LOGGER = logging.getLogger(__name__)

class PufferPanelClient:
    def __init__(self, host, port, client_id, client_secret, session, use_https=False):
        protocol = "https" if use_https else "http"
        port_int = int(float(port))
        self.base_url = f"{protocol}://{host}:{port_int}/api"
        self.auth_url = f"{protocol}://{host}:{port_int}/oauth2/token"
        self.client_id = client_id
        self.client_secret = client_secret
        self.session = session
        self.token = None



    async def authenticate(self):
        """Exchange Client ID and Secret for a Bearer Token."""
        auth_data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        try:
            async with self.session.post(self.auth_url, data=auth_data) as resp:
                if resp.status == 200:
                    res_json = await resp.json()
                    self.token = res_json.get("access_token")
                    _LOGGER.debug("PufferPanel authentication successful")
                    return True
                
                _LOGGER.error("PufferPanel auth failed with status %s", resp.status)
                return False
        except Exception as e:
            _LOGGER.error("Exception during PufferPanel authentication: %s", e)
            return False
    
    async def _get(self, endpoint):
        """Internal helper to handle authentication and URL building."""
        if not self.token:
            await self.authenticate()
        url = f"{self.base_url}{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {self.token}", 
            "Accept": "application/json"
        }
        
        try:
            async with asyncio.timeout(10):
                async with self.session.get(url, headers=headers) as resp:
                    if resp.status == 401:
                        await self.authenticate()
                        return await self._get(endpoint)
                    if resp.status == 204:
                        return {}
                    if resp.status == 200:
                        return await resp.json()
                    return None
        except Exception as e:
            _LOGGER.error("PufferPanel connection error: %s", e)
            return None
            

    async def get_servers(self):
        response = await self._get("/servers")
        if response is None:
            _LOGGER.error("PufferPanel API returned None for /servers")
            return {"servers": []}
            
        return response

    async def get_server_status(self, server_id):
        return await self._get(f"/servers/{server_id}/status")

    async def get_server_stats(self, server_id):
        return await self._get(f"/servers/{server_id}/stats")

    async def get_server_query(self, server_id):
        return await self._get(f"/servers/{server_id}/query")

    async def get_server_flags(self, server_id):
        return await self._get(f"/servers/{server_id}/flags")

    async def get_server_data(self, server_id):
        return await self._get(f"/servers/{server_id}/data")

    async def _post(self, path, json_data=None):
        """Internal helper for POST requests."""
        if not self.token:
            await self.authenticate()
            
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }
        
        try:
            async with self.session.post(url, json=json_data, headers=headers) as response:
                if response.status in [200, 204]:
                    try:
                        import json
                        return json.loads(data) if data else {}
                    except:
                        return {}
                
                _LOGGER.error("PufferPanel POST %s failed: %s", path, response.status)
                return {}
        except Exception as e:
            _LOGGER.error("PufferPanel connection error during POST: %s", e)
            return {}

    async def send_server_action(self, server_id, action):
        return await self._post(f"/servers/{server_id}/{action}", json_data={})

# --- INTERACTIVE TEST BLOCK ---
if __name__ == "__main__":
    print("\n--- PufferPanel API Interactive Tester ---")
    
    host_in = input("Host (e.g 192.168.x.x): ").strip()
    port_in = input("Port (default 8080): ").strip() or "8080"
    c_id = input("Client ID: ").strip()
    c_sec = input("Client Secret: ").strip()
    use_https = (input("Use HTTPS? (y/N): ").lower().strip() or "n") == 'y'

    async def run_test():
        async with aiohttp.ClientSession() as session:
            client = PufferPanelClient(host_in, port_in, c_id, c_sec, session, use_https)
        
            print("\nAttempting to authenticate...")
            if await client.authenticate():
                print("Authentication Successful \n")

                print("Fetching servers...")
                res = await client.get_servers()
                servers = res.get("servers", []) if res else []
                print(f"Found {len(servers)} servers\n")
                
                print(f"{'NAME':<20} | {'TYPE':<15} | {'ID':<10} | {'CPU':<6} | {'RAM'}")
                print("-" * 50)
                
                for s in servers:
                    sid = s['id']
                    status = await client.get_server_status(sid)
                    
                    if not status or not status.get("running"):
                        print(f"{s['name']:<20} | {'Offline':<10}")
                    else:
                        stats = await client.get_server_stats(sid)
                        
                        if stats is None:
                            print(f"{s['name']:<20} | Offline")
                        else:
                            cpu = round(stats.get('cpu', 0), 2)
                            cpu_str = f"{cpu}%"
                            mem_raw = round(stats.get('memory', 0), 2)
                            mem_converted = round(mem_raw / (1024 ** 3), 2)
                            mem_str = f"{mem_converted}GB"
                            print(f"{s['name']:<20} | {s['type']:<15} | {s['id']:<10} | {cpu_str:<6} | {mem_str}")
            else:
                print("Authentication failed. Check credentials.")

    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        print("\nTest cancelled.")
        sys.exit(0)
