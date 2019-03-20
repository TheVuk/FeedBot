# need to enable when running from terminal
# import sys
# import os
# sys.path.append(os.getcwd())

import traceback
import time
import threading
from src.loghandler import log
from src.main.fb_objects import FBObjects as Fb_Obj
from src.nsehelper.nse_commons import NseCommons
from src.ibservices.ib_services import IBService


# setting up general logger
logger = log.setup_custom_logger('root')
nse_com = NseCommons()
ib_conn = IBService()
TWS_IP = Fb_Obj.parser.get('common', 'gateway_ip')
TMS_PORT = int(Fb_Obj.parser.get('common', 'gateway_port'))
IB_CLIENT_ID = int(Fb_Obj.parser.get('common', 'IB_ClientId'))
TIME_INTERVAL = int(Fb_Obj.parser.get('common', 'time_interval'))


class IBSubscriptionThread(object):

    LAST_SUBSCRIPTION_ID = 0
    TIME_INTERVAL = 0

    def ib_subscription_thread(self, interval=60):
        self.TIME_INTERVAL = interval
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()
        return thread

    def run(self):
        try:
            while not Fb_Obj.STOP_NSE_TOOL:
                if (len(Fb_Obj.TOP_MOVERS) != 0) and Fb_Obj.TOP_MOVERS is not None:
                    for mover in enumerate(Fb_Obj.TOP_MOVERS):
                        try:
                            if (Fb_Obj.TOP_MOVERS.get(mover[1])) == 'None':
                                sub_id = self.LAST_SUBSCRIPTION_ID + 1
                                contract = ib_conn.get_stk_Contract(mover[1])
                                ib_conn.reqMktData(sub_id, contract, "233", False, False, [])
                                logger.info("Tick Data Requested for %s" % mover[1])
                                logger.info("Tick Data Request ID:"+str(sub_id))
                                self.LAST_SUBSCRIPTION_ID = sub_id
                                Fb_Obj.TOP_MOVERS[mover[1]] = sub_id
                                # returned_value = os.system("kafka-topics --create --zookeeper "
                                #                            "localhost:2181 --replication-factor 1 --partitions 1 -"
                                #                            "-topic %s" % str(sub_id))
                                # logger.info("Kafka Topic Created: %s" % returned_value)
                        except:
                            logger.error("IB Subscription Error Happening for %s" % str(mover))
                            logger.error(traceback.format_exc())
                    logger.info(Fb_Obj.TOP_MOVERS)
                    time.sleep(TIME_INTERVAL+60)
                    self.run()
        except Exception as ex:
            logger.error(ex)
            logger.error(traceback.format_exc())
            self.run()


class FeedBot(object):

    @staticmethod
    def connect_ib():
        try:
            if not ib_conn.isConnected():
                ib_conn.connect(TWS_IP, TMS_PORT, clientId=IB_CLIENT_ID)
                logger.info("serverVersion:%s connectionTime:%s" % (ib_conn.serverVersion(), ib_conn.twsConnectionTime()))
        except Exception as ex:
            logger.error(ex)
            logger.error(traceback.format_exc())


def main():
    try:
        logger.info("Preparing to start IB Service Provider")
        logger.info("IB GateWay info IP:PORT - " + str(Fb_Obj.parser.get('common', 'gateway_ip')
                                                       + ":" + str(Fb_Obj.parser.get('common', 'gateway_port'))))
        bb_bot = FeedBot()
        bb_bot.connect_ib()

        # Debug Codes
        # con = ib_conn.get_stk_Contract("BHARTIARTL")
        # ib_conn.reqMktData(1, con, "233", False, False, [])

        nse_corn_thread = nse_com.top_mover_thread(TIME_INTERVAL)
        logger.info("Started to get top movers from NSE corn thread")
        time.sleep(20)
        ib_sub = IBSubscriptionThread()
        ib_sub_thread = ib_sub.ib_subscription_thread(TIME_INTERVAL)
        logger.info("Started tick data subscriber thread from broker bot")
        logger.info("NSE Corn Thread Status %s" % str(nse_corn_thread.isAlive()))
        logger.info("IB Subscription Corn Thread Status %s" % str(ib_sub_thread.isAlive()))
        ib_conn.run()
        time.sleep(30)

        # Debug Codes
        # To exit all the Thread
        # Fb_Obj.STOP_NSE_TOOL = True
    except Exception as ex:
        logger.error(ex)
        logger.error(traceback.format_exc())


if __name__ == '__main__':
    logger.info("**FeedFeedBot Initiated")
    main()

