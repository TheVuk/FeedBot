from src.ibservices.ib_client_wrap import IBClient, IBWrapper
from src.brokerlib.ibapi.utils import iswrapper
from src.brokerlib.ibapi.contract import *
from src.brokerlib.ibapi.common import *
from src.brokerlib.ibapi.ticktype import *
from json import dumps
from kafka import KafkaProducer
import json
import os
import traceback
import datetime
import logging
import queue

logger = logging.getLogger('root')
DEFAULT_GET_CONTRACT_ID=43

# marker for when queue is finished

FINISHED = object()
STARTED = object()
TIME_OUT = object()

SYM_MAP_PATH = os.path.dirname(os.environ['FEEDBOT_CONFIG'])+os.sep+"IB_NSE_Map.json"

producer = KafkaProducer(bootstrap_servers=['127.0.0.1:9092'],
                         value_serializer=lambda x:
                         dumps(x).encode('utf-8'))


class FinishableQueue(object):

    def __init__(self, queue_to_finish):

        self._queue = queue_to_finish
        self.status = STARTED

    def get(self, timeout):
        """
        Returns a list of queue elements once timeout is finished, or a FINISHED flag is received in the queue
        :param timeout: how long to wait before giving up
        :return: list of queue elements
        """
        contents_of_queue=[]
        finished=False

        while not finished:
            try:
                current_element = self._queue.get(timeout=timeout)
                if current_element is FINISHED:
                    finished = True
                    self.status = FINISHED
                else:
                    contents_of_queue.append(current_element)
                    ## keep going and try and get more data

            except queue.Empty:
                # If we hit a time out it's most probable we're not getting a finished element any time soon
                # give up and return what we have
                finished = True
                self.status = TIME_OUT


        return contents_of_queue

    def timed_out(self):
        return self.status is TIME_OUT


class IBService(IBWrapper, IBClient):
    def __init__(self):
        try:
            IBWrapper.__init__(self)
            IBClient.__init__(self, wrapper=self)
            self._my_contract_details = {}
        except Exception as ex:
            logger.error(ex)
            logger.error(traceback.format_exc())

    # ! [getting IB server current time]
    @iswrapper
    def currentTime(self, time: int):
        try:
            super().currentTime(time)
            print("CurrentTime:", datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"))
        except Exception as ex:
            logger.error(ex)
            logger.error(traceback.format_exc())

    @iswrapper
    # ! [Getting Tick-by-Tick Data from IB Instrument subscribtion]
    def tickByTickAllLast(self, reqId: int, tickType: int, time: int, price: float,
                          size: int, tickAtrribLast: TickAttribLast, exchange: str,
                          specialConditions: str):
        super().tickByTickAllLast(reqId, tickType, time, price, size, tickAtrribLast,
                                  exchange, specialConditions)
        if tickType == 1:
            print("Last.", end='')
        else:
            print("AllLast.", end='')
        print(" ReqId:", reqId,
              "Time:", datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"),
              "Price:", price, "Size:", size, "Symbol:")

    ## get contract details code
    def init_contractdetails(self, reqId):
        contract_details_queue = self._my_contract_details[reqId] = queue.Queue()

        return contract_details_queue

    def contractDetails(self, reqId, contractDetails):
        ## overridden method

        if reqId not in self._my_contract_details.keys():
            self.init_contractdetails(reqId)

        self._my_contract_details[reqId].put(contractDetails)

    def resolve_ib_contract(self, ibcontract, reqId=DEFAULT_GET_CONTRACT_ID, retry=True):
        """
        From a partially formed contract, returns a fully fledged version
        :returns fully resolved IB contract
        """
        ## Make a place to store the data we're going to return
        contract_details_queue = FinishableQueue(self.init_contractdetails(reqId))
        print("Getting full contract details from the server... ")
        self.reqContractDetails(reqId, ibcontract)
        # Run until we get a valid contract(s) or get bored waiting
        MAX_WAIT_SECONDS = 2
        new_contract_details = contract_details_queue.get(timeout=MAX_WAIT_SECONDS)
        # while IBWrapper.is_error():
        #     logger.error(self.get_error())
        if contract_details_queue.timed_out():
            logger.warn("Exceeded maximum wait for wrapper to confirm finished - seems to be normal behaviour")
        if len(new_contract_details) == 0:
            logger.error("Failed to get contract details: Trying to Cross Verify With Symbol Map Json")
            if retry:
                ibcontract.symbol = self.get_ibsymbol_from_map(ibcontract.symbol)
                ibcontract = self.resolve_ib_contract(ibcontract, retry=False)
            return ibcontract
        if len(new_contract_details) > 1:
            logger.error("got multiple contracts using first one")
        new_contract_details = new_contract_details[0]
        resolved_ibcontract = new_contract_details.contract
        return resolved_ibcontract

    def get_ibsymbol_from_map(self, nsesymbol):
        try:
            map_json = json.loads(open(str(SYM_MAP_PATH)).read())
            for sym in map_json:
                if sym['NSE_Symbol'] == nsesymbol:
                    return sym['IB_Symbol']
            return nsesymbol
        except Exception as ex:
            logger.error("No mapping value found for NSE Symbol:%s" % nsesymbol)
            logger.error(traceback.format_exc())

    def get_stk_Contract(self, symbol):
        try:
            contract = Contract()
            contract.symbol = self.get_ibsymbol_from_map(symbol)
            contract.secType = "STK"
            contract.currency = "INR"
            contract.exchange = "NSE"
            return contract #self.resolve_ib_contract(contract)
        except Exception as ex:
            logger.error(ex)
            logger.error(traceback.format_exc())

    @iswrapper
    # ! [contractdetailsend]
    def contractDetailsEnd(self, reqId: int):
        super().contractDetailsEnd(reqId)
        print("ContractDetailsEnd. ReqId:", reqId)

    @iswrapper
    # ! [tickstring]
    def tickString(self, reqId: TickerId, tickType: TickType, value: str):
        super().tickString(reqId, tickType, value)
        try:
            if tickType == 48:
                if value.split(';')[0] != '':
                    price = value.split(';')[0]
                    size = value.split(';')[1]
                    timestamp = datetime.datetime.fromtimestamp(int(value.split(';')[2])/1000.0).strftime('%Y-%m-%d %H:%M:%S')
                    tottrade = value.split(';')[3]
                    VWAP = value.split(';')[4]
                    data = {'Price': price, 'Timestamp': timestamp, 'tottrade': tottrade, 'VWAP': VWAP}
                    producer.send(str(reqId), value=data)
                # else:
                #     print(value)
        except Exception as ex:
            logger.error(traceback.format_exc())

