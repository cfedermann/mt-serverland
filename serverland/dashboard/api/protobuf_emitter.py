'''
Google Protobuf emitter the serverland dashboard API.
Project: MT Server Land prototype code
 Author: Will Roberts <William.Roberts@dfki.de>

'''

from base64 import b64encode
from piston.emitters import Emitter
from serverland.protobuf.TranslationRequestMessage_pb2 import \
     TranslationRequestMessage, TranslationRequestObject, \
     TranslationRequestList
from serverland.protobuf.WorkerServerMessage_pb2 import \
     WorkerServerObject, WorkerServerList

class ProtobufEmitter(Emitter):
    '''
    Protobuf emitter.
    '''

    @staticmethod
    def dict_to_tro(dict_obj):
        '''
        Converts a dictionary representation into a
        TranslationRequestObject protobuf.
        '''
        tr_obj = TranslationRequestObject()
        defined_keys = set(['blah', 'shortname', 'request_id',
                            'worker', 'owner', 'created', 'ready',
                            'result', 'source_language',
                            'target_language'])
        tr_obj.shortname = dict_obj['shortname']
        tr_obj.request_id = dict_obj['request_id']
        tr_obj.worker = dict_obj['worker']
        tr_obj.owner = dict_obj['owner']
        tr_obj.created = dict_obj['created'].isoformat()
        tr_obj.ready = dict_obj['ready']
        if 'result' in dict_obj:
            result_obj = TranslationRequestMessage()
            result_obj.request_id = dict_obj['request_id']
            result_obj.source_language = dict_obj['source_language']
            result_obj.target_language = dict_obj['target_language']
            result_obj.source_text = ''
            result_obj.target_text = dict_obj['result']
            for key in set(dict_obj.keys()) - defined_keys:
                kv_pair = result_obj.packet_data.add()
                kv_pair.key = key
                kv_pair.value = dict_obj[key]
            tr_obj.serialized = b64encode(result_obj.SerializeToString())
        else:
            tr_obj.serialized = ''
        return tr_obj

    @staticmethod
    def dict_to_wso(dict_obj):
        '''
        Converts a dictionary representation into a
        WorkerServerObject protobuf.
        '''
        ws_obj = WorkerServerObject()
        ws_obj.shortname = dict_obj['shortname']
        ws_obj.description = dict_obj['description']
        ws_obj.is_alive = dict_obj['is_alive']
        if 'is_busy' in dict_obj:
            ws_obj.is_busy = dict_obj['is_busy']
        else:
            ws_obj.is_busy = False
        if 'language_pairs' in dict_obj:
            for (source_lang, target_lang) in dict_obj['language_pairs']:
                langpair = ws_obj.language_pairs.add()
                langpair.source = source_lang
                langpair.target = target_lang
        return ws_obj

    def render(self, _request):
        '''
        Renders a response from the serverland API to a b64-encoded
        serialized protobuf.
        '''
        value = self.construct()
        pbuf = None
        if ( isinstance(value, list) and
             len(value) > 0 and
             isinstance(value[0], dict) ):
            if 'is_alive' in value[0]:
                pbuf = WorkerServerList()
                for listitem in value:
                    item = pbuf.workers.add()
                    item.CopyFrom(ProtobufEmitter.dict_to_wso(listitem))
            elif 'request_id' in value[0]:
                pbuf = TranslationRequestList()
                for listitem in value:
                    item = pbuf.requests.add()
                    item.CopyFrom(ProtobufEmitter.dict_to_tro(listitem))
        elif isinstance(value, dict):
            if 'is_alive' in value:
                pbuf = ProtobufEmitter.dict_to_wso(value)
            elif 'request_id' in value:
                pbuf = ProtobufEmitter.dict_to_tro(value)

        if pbuf:
            return b64encode(pbuf.SerializeToString())
        else:
            return ''

Emitter.register('protobuf', ProtobufEmitter, 'application/x-protobuf')
