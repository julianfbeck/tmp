from webbrowser import get
from twisted.internet import reactor
from quarry.net.client import ClientFactory, ClientProtocol
from kafka import KafkaProducer, KafkaConsumer
from json import dumps, loads
import os
kafka_string = os.environ.get('KAFKA_URL')
if kafka_string is None:
    kafka_string = "localhost:9092"
producer = KafkaProducer(bootstrap_servers=[kafka_string],
                                api_version=(0, 10, 2),
                         value_serializer=lambda x: 
                         dumps(x).encode('utf-8'))
                    
def get_status(ip):
    class PingProtocol(ClientProtocol):

        def status_response(self, status):
            text = ""
            version = ""
            online = -1
            players = []
            modded = False 
            if "description" in status and "text" in status["description"]:
                text = status["description"]["text"]
            if  "version" in status and "name" in status["version"]:
                version = status["version"]["name"]
            if "favicon" in status:
                status["favicon"] =""
            if "modinfo" in status or "forgeData" in status:
                modded = True         
            if "players" in status and "online" in status["players"]:
                online = status["players"]["online"]
                if "sample" in status["players"]:
                    for player in status["players"]["sample"]:
                        player = {
                            "name": player.get("name", "-undefined"),
                            "uuid": player.get("id", "-undefined"),
                            "server": ip,
                            "modded":modded,
                            "version":version,
                            "text": text
                        }
                        producer.send("players", value=player)
                        producer.flush()
                        players.append({
                            "name": player.get("name", "-undefined"),
                            "uuid": player.get("id", "-undefined")}
                        )
            server = {"ip": ip, "text": text, "version": version, "online": online, "modded": modded, "players": players, "status": status}
            print("server:", ip)
            producer.send("server-values", value=server)
            producer.flush()
            reactor.stop()


    class PingFactory(ClientFactory):
        protocol = PingProtocol
        protocol_mode_next = "status"


    factory = PingFactory()
    factory.connect(ip, 25565)
    print("connection")
    reactor.run()

if __name__ == "__main__":
    print("Starting pinger")
    # get ip from args
    import sys
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--ping",  help="ping host")
    args = parser.parse_args(sys.argv[1:])
    get_status(args.ping)
