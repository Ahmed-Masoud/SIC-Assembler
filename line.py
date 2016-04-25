class Line:
    _label = None
    _directive = None
    _operand = None
    _objectCode = None
    _address = None
    _equ = 0

    def __init__(self, label, directive, operand):
        self._label = label
        self._directive = directive
        self._operand = operand

    def setLabel(self, label):
        self._label = label

    def getLabel(self):
        return self._label

    def getCleanLabel(self):
        return self._label.rstrip().lower()

    def setDirective(self, directive):
        self._directive = directive

    def getDirective(self):
        return self._directive

    def getCleanDirective(self):
        return self._directive.rstrip().lower()

    def setOperand(self, operand):
        self._operand = operand

    def getOperand(self):
        return self._operand

    def getCleanOperand(self):
        return self._operand.rstrip().lower()

    def setObjectCode(self, objectCode):
        self._objectCode = objectCode

    def getObjectCode(self):
        return self._objectCode

    def setAddress(self, address):
        self._address = address

    def getAddress(self):
        return self._address

    def getCleanAddress(self):
        return self._address.rstrip().lower()

    def setEqu(self, equ):
        self._equ = equ

    def getEqu(self):
        return self._equ