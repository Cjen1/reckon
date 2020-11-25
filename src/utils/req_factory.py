import src.utils.message_pb2 as Msg


class ReqFactory(object):
    @staticmethod
    def finalise():
        finalise = Msg.Request()
        finalise.finalise.msg = ""
        return finalise

    @staticmethod
    def start():
        start = Msg.Request()
        start.start.msg = ""
        return start

    @staticmethod
    def write(key, value, start, prereq=False):
        putOp = Msg.Request()
        putOp.op.put.key = key
        putOp.op.put.value = value
        putOp.op.start = start
        putOp.op.prereq = prereq
        return putOp

    @staticmethod
    def read(key, start, prereq=False):
        getOp = Msg.Request()
        getOp.op.get.key = key
        getOp.op.start = start
        getOp.op.prereq = prereq
        return getOp
