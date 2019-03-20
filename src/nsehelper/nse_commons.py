import threading
import time
import logging
import traceback
from nsetools import Nse
from src.main.fb_objects import FBObjects as FbObj
logger = logging.getLogger('root')


class NseCommons(object):
    nse_obj = Nse()
    interval = 0

    def corn_job(self):
        try:
            while not FbObj.STOP_NSE_TOOL:
                try:
                    gainers = self.nse_obj.get_top_gainers()
                    for gainer in gainers:
                        if gainer.get("symbol") not in FbObj.TOP_MOVERS.keys():
                            FbObj.TOP_MOVERS[gainer.get("symbol")] = "None"
                    losers = self.nse_obj.get_top_losers()
                    for loser in losers:
                        if loser.get("symbol") not in FbObj.TOP_MOVERS.keys():
                            FbObj.TOP_MOVERS[loser.get("symbol")] = "None"
                    # logger.info(FbObj.TOP_MOVERS)
                    time.sleep(self.interval)
                    self.corn_job()
                except Exception as ex:
                    logger.error(ex)
                    logger.error(traceback.format_exc())
        except Exception as ex:
            logger.error(ex)
            logger.error(traceback.format_exc())

    def top_mover_thread(self, interval=60):
        try:
            logger.info("Trying to get top market movers")

            """ Constructor
            :type interval: int
            :param interval: Check interval, in seconds
            """
            self.interval = interval
            thread = threading.Thread(target=self.corn_job, args=())
            thread.daemon = True  # Daemonize thread
            thread.start()
            return thread
        except Exception as ex:
            logger.error(ex)
            logger.error(traceback.format_exc())

