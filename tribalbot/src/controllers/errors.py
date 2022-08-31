from tribalbot.src.errors import TribeBotBaseException

class TribeBotControllerError(TribeBotBaseException): pass

class BadTribeCategory(TribeBotControllerError): pass

class InvalidMember(TribeBotControllerError): pass

