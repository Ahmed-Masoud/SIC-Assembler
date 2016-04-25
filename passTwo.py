######################### PASS TWO #########################

'''
pass two does real translation and assembling
and writes both object and assembly listing files
'''
import util

endRecord = False
hasError = False

def assemble():
    """
    assembles each line of instructions and
    produces its object code
    """

    lines = util.linesListWithData

    # check for errors first before generating object code
    validateErrors()

    lastDirective = ""

    for line in lines:
        # skip if comment
        if (line.getLabel()[0] == ".") or (line.getCleanDirective() == "org"):
            continue

        # skip if line has errors
        address = line.getAddress()
        directive = line.getCleanDirective()
        if (len(util.errorsTable[address]) > 0) and (lastDirective != "equ"):
            lastDirective = directive
            continue

        if line.getCleanDirective() == "equ":
            continue

        # initialize object code
        objCode = None

        ## get operation code
        opCode = None

        # start has no object code (null)
        if directive == "start":
            line.setObjectCode(objCode)
            # go to next line of instructions
            continue
        # normal directive
        # make sure operation is present in operations table
        elif directive in util.opTable:
            opCode = util.opTable[directive]

        ## get address
        if opCode is not None:
            operand = line.getCleanOperand()
            index = operand.find(",")

            # indexing is used
            if index != -1:
                temp = operand[:index]
                address = util.symTable[temp][0]
            # no indexing
            else:
                if directive != "rsub":
                    if operand in util.symTable.keys():
                        address = util.symTable[operand][0]
                else:
                    address = "0000"
            # if indexing is used add value of 'x' bit to address
            if ",x" in operand:
                address = int(address, 16)
                address += int("8000", 16)
                address = hex(address)[2:]

            # calculate object code
            objCode = opCode + address

        ## handle 'WORD' & 'BYTE'
        if opCode is None:
            if directive == "word":
                if line.getCleanOperand() in util.symTable.keys():
                    operand = util.symTable[line.getCleanOperand()][0]
                    operand = fixHexString(operand, 6)
                elif (line.getCleanOperand() not in util.symTable.keys()) and \
                        (not line.getCleanOperand().isdigit()):
                    operand = "      "
                else:
                    # get value and change it to hexadecimal
                    operand = hex(int(line.getCleanOperand()))[2:]
                    # make sure value is 6 hexadecimal digits (1 word)
                    operand = fixHexString(operand, 6)
                # calculate object code
                objCode = operand

            elif directive == "byte":
                operand = line.getCleanOperand()
                # normal string
                if operand[0] == 'c':
                    operand = operand[2:-1]
                    address = ""
                    # change string characters to their ascii hexadecimal values
                    for c in operand:
                        address += str(hex(ord(c))[2:])
                # hexadecimal string
                elif operand[0] == 'x':
                    address = operand[2:-1]

                # calculate object code
                objCode = address

        lastDirective = directive

        ## add object code to line
        line.setObjectCode(objCode)

    util.linesListWithData = lines

    writeObjFile()
    writeListFile()

def fixHexString(num, limit):
    """
    makes sure that num has a length of limit
    """

    zero = "0"
    count = limit - len(num)
    num = (zero * count) + num
    return num

def writeObjFile():
    """
    writes formatted object code to file
    """

    file = open("OBJFILE", "w+")

    lines = util.linesListWithData
    # check if program didnt start with start
    if lines[0].getCleanDirective() != "start":
        file.write(" ")
        return

    # write header record
    progName = lines[0].getLabel()[:-2]
    startAdrs = lines[0].getAddress()
    if len(startAdrs) < 6:
        startAdrs = fixHexString(startAdrs, 6)

    # calculate length of program by finding the difference between last and first address
    lengthOfProg = hex(int(lines[-1].getAddress(), 16) - int(lines[0].getAddress(), 16))[2:]
    if len(lengthOfProg) < 6:
        lengthOfProg = fixHexString(lengthOfProg, 6)

    headerStr = "H" + progName + startAdrs + lengthOfProg + "\n"

    file.write(headerStr)

    # check if program has errors no text records are generated
    global hasError
    if hasError:
        return

    # write text records
    writeTextRecord(file, lines[1:])

    # write end record
    endRecordStr = "E" + startAdrs
    file.write(endRecordStr)
    file.close()

def writeTextRecord(file, lines):
    """
    recursive method that writes text records
    """

    # finished writing records
    if lines == []:
        # set global boolean and return
        global endRecord
        endRecord = True
        return

    if lines[0].getLabel() == ".":
        writeTextRecord(file, lines[1:])

    startAdrs = lines[0].getAddress()
    if startAdrs is not None:
        if len(startAdrs) < 6:
            startAdrs = fixHexString(startAdrs, 6)

    # start writing new text record

        textRecordStr = "T" + startAdrs


    # string to accumulate object code of the record in
    objCodeStr = ""

    # loop on each line of instructions
    for i in range(0, (len(lines))):
        if (lines[i].getLabel()[0] == ".") or (lines[i].getCleanDirective() == "equ"):
            continue

        currentObjCode = lines[i].getObjectCode()
        # before last line
        if i == (len(lines) - 1):
            nextObjCode = None
        else:
            nextObjCode = lines[i + 1].getObjectCode()

        '''
        if (currentObjCode is None) and (nextObjCode is None):
            continue
        '''

        # current line doesn't have object code
        # must terminate and start a new record
        if currentObjCode is None:
            # get length of record
            length = hex(len(objCodeStr) / 2)[2:]
            if len(length) < 2:
                length = fixHexString(length, 2)
            # get object code of record
            textRecordStr += length + objCodeStr + "\n"
            if objCodeStr != '':
                file.write(textRecordStr)
            # terminate and start a new record
            writeTextRecord(file, lines[i + 1:])

        # return when finished writing
        if endRecord:
            return

        # accumulate object code to terminate in next loop
        if nextObjCode is None:
            objCodeStr += currentObjCode
            continue

        if currentObjCode is not None:
            objCodeStr += currentObjCode

        # length of record bigger than 60
        # must terminate and start a new record
        if (len(objCodeStr) + len(nextObjCode) > 60):
            # get length of record
            length = hex(len(objCodeStr) / 2)[2:]
            if len(length) < 2:
                length = fixHexString(length, 2)
            # get object code of record
            textRecordStr += length + objCodeStr + "\n"
            if objCodeStr != '':
                file.write(textRecordStr)
            # terminate and start a new record
            writeTextRecord(file, lines[i + 1:])

def writeListFile():
    """
    writes list file
    """

    file = open("LISFILE", "w+")

    lines = util.linesListWithData
    lastDirective = ""

    for line in lines:
        # if comment write as is
        if line.getLabel()[0] == ".":
            file.write((12 * " ") + line.getLabel() + "\n")
            continue

        # if org write as it is
        if line.getCleanDirective() == "org":
            address, label, directive, operand = "     ", line.getLabel(), line.getDirective(), line.getOperand()
            file.write((6 * " ") + address + " " + label + " " + directive + " " + operand + "\n")

            if line.getCleanOperand() in util.symTable.keys() or \
                    line.getCleanOperand().isdigit() or \
                            line.getCleanOperand() == '':
                continue
            else:
                file.write("\t\t****** undefined in operand\n")
                continue

        # if line has errors print line as is with its errors
        address = line.getAddress()
        cleanDirective = line.getCleanDirective()

        if (len(util.errorsTable[address]) > 0) and (cleanDirective not in ["start", "end"]):
            address, label, directive, operand = line.getAddress(), line.getLabel(), line.getDirective(), line.getOperand()
            objCode = line.getObjectCode()
            if objCode is not None:
                objCode = fixHexString(objCode, 6)
                lineStr = address + " " + objCode + " " + label + " " + directive + " " + operand + "\n"
            else:
                lineStr = address + (8 * " ") + label + " " + directive + " " + operand + "\n"
            file.write(lineStr)

            if (cleanDirective == "equ"):
                for i in range(0, len(util.errorsTable[address]) - 1, 2):
                    if (line.getEqu() == util.errorsTable[address][i + 1]):
                        file.write("\t\t******* " + util.errorsTable[address][i] + "\n")
            else:
                for msg in util.errorsTable[address]:
                    # handle if first instruction after equ
                    # don't print error twice
                    # if (type(msg) is not int) and (lastDirective != "equ"):
                    if lastDirective != "equ":
                        file.write("\t\t******* " + msg + "\n")

            lastDirective = cleanDirective
            continue

        # get parts of line
        address, label, directive, operand, objCode = line.getAddress(), line.getLabel(), line.getDirective(), line.getOperand(), line.getObjectCode()

        # set object code spaces
        if objCode is None:
            objCode = "      "

        # increase length to 6 digits
        if len(objCode) < 6:
            diff = 6 - len(objCode)
            objCode = objCode + (" " * diff)

        # print multi-line object code
        if len(objCode) > 6:
            length = len(objCode)
            temp = objCode
            temp = temp[0:6]
            # print first normal line
            lineStr = address + " " + temp + " " + label + " " + directive + " " + operand + "\n"
            file.write(lineStr)
            # loop on remaining object code with limit of 6 as step
            for i in range(6, length, 6):
                # set space before string
                str = (" " * len(address)) + " "
                temp = objCode
                # if object code has more than 6 remaining digits print only 6
                if i + 6 < len(objCode):
                    str += temp[i:i + 6] + "\n"
                # if object code has less than 6 remaining digits print the remaining
                else:
                    diff = (i + 6) - len(objCode)
                    str += temp[i:i + (6 - diff)] + "\n"
                file.write(str)

        # object code has length of 6
        else:
            lineStr = address + " " + objCode + " " + label + " " + directive + " " + operand + "\n"
            file.write(lineStr)

    file.close()

def validateErrors():
    """
    still not done
    """

    global hasError

    lines = util.linesListWithData

    # check if anything before "start"
    if lines[0].getCleanDirective() != "start":
        util.errorsTable[lines[0].getAddress()] = ["statement should not precede start statement",
                                                   "missing or misplaced start statement"]
        hasError = True

    for line in lines:
        errorList = []
        # if line precedes start

        # skip if comment or org
        if (line.getLabel()[0] == ".") or \
                (line.getCleanDirective() == "org") or \
                (line.getCleanDirective() == "equ"):
            continue

        address, label, directive, operand = line.getAddress(), line.getLabel(), line.getDirective(), line.getOperand()

        # check blank line
        if (label == "\r" and directive == "" and operand == ""):
            errorList.append("missing operation code")
            errorList.append("unrecognized operation code")
            errorList.append("missing or misplaced operand in instruction")
            util.errorsTable[address] = errorList
            hasError = True
            continue

        ## check directive errors
        directive = directive.rstrip().lower()
        # directive is empty
        if (directive == "") or (directive is None):
            errorList.append("missing operation code")
        # pass if directive is a reserved operation with no hexadecimal code
        elif (directive in ["start", "byte", "word", "resw", "resb", "end"]):
            pass
        elif directive.replace(" ", "") == "equ":
            pass
        # directive isn't in operations table
        elif directive not in util.opTable.keys():
            errorList.append("unrecognized operation code")
            errorList.append("illegal operation code format")

        ## check label errors
        if (label.rstrip() != ""):
            # duplicate label found
            if moreThanOnce(label):
                errorList.append("duplicate label definition")
        # label contains spaces
        if (" " in label.rstrip()):
            errorList.append("illegal format in label field")
        # label should be defined but not
        elif (directive in ["byte", "word", "resw", "resb"]) and (label.rstrip() == ""):
            errorList.append("illegal format in label field")
        # check if first digit is a number
        elif label[0].isdigit():
            errorList.append("illegal format in label field")

        ## check operand errors
        operand = operand.rstrip().lower()
        index = operand.find(",")
        if index != -1:
            operand = operand[:index]
        # pass if operand is string
        if (operand[:2] in ["c'", "x'"]) and (operand[-1] == '\'') and (directive == "byte"):
            pass

        # operand should contain a number
        if directive != "rsub":
            if operand == "":
                errorList.append("missing or misplaced operand in instruction")
            elif (not operand[0].isdigit()) and (directive in ["word", "resw", "resb"]) and \
                    (operand not in util.symTable.keys()):
                errorList.append("illegal operand field")
        # operand contains spaces or not found in symbol table or should not be a number
        if ((" " in operand) or (operand not in util.symTable.keys()) or (operand[0].isdigit())) and \
                (directive not in ["word", "resw", "resb", "start", "end", "rsub", "byte"]):
            if directive.rstrip().lower() != "rsub":
                errorList.append("missing or misplaced operand in instruction")
                errorList.append("illegal operand field")

        # check if line has errors
        if (len(errorList) > 0):
            # set global variable
            hasError = True

        if address != "0000":
            if (address in util.errorsTable.keys()) and (len(util.errorsTable[address]) > 0):
                util.errorsTable[address] += errorList
            else:
                util.errorsTable[address] = errorList

    # check if anything after "end"
    if lines[-1].getCleanDirective() != "end":
        util.errorsTable[lines[-1].getAddress()] = ["statement should not follow end statement",
                                                    "missing or misplaced end statement"]
        hasError = True

def moreThanOnce(symbol):
    """
    checks if label is present
    more than once in code
    """

    counter = 0
    lines = util.linesListWithData
    for line in lines:
        if line.getCleanLabel() == symbol.strip().lower():
            counter += 1

    return counter > 1
