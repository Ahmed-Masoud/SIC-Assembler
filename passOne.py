######################### PASS ONE #########################

'''
pass one assigns address to each instruction
and constructs a symbol table
'''

import util
import passTwo
from line import Line
import re

def stringInstructionsToLists(instruction):
    """
    splits an instruction string and returns it
    as list of strings
    """

    return Line(instruction[0:8], instruction[9:17], instruction[17:36])

def readFromFile():
    """
    reads the srcfile, saves all the code as lists of
    string using the function 'stringInstructionsToLists'
    then calls 'assignAddresses'
    """

    file = open("SRCFILE", "r+")

    # get line by line
    lines = [line.rstrip('\n') for line in file]

    linesList = []

    for line in lines:
        # if line is comment put as is
        if line[0] == '.':
            linesList.append(Line(line, None, None))
        # process normal line
        else:
            linesList.append(stringInstructionsToLists(line))

    assignAddresses(linesList)

def assignAddresses(linesList):
    """
    assigns an address to each instruction
    """
    endCame = False
    noStart = False
    adrressNotAssigned = False
    errorAddress = "0000"
    equCounter = 0

    # get start address as hex number but check if first line is start
    if linesList[0].getCleanDirective() != "start":
        linesList[0].setAddress(errorAddress)
        # util.errorsTable["0000"] = ["missing or misplaced start statement"]
        noStart = True
    else:
        startingAddress = int(linesList[0].getOperand(), 16)
        currentAddress = startingAddress

    for line in linesList:
        # skip if comment
        if line.getLabel()[0] == '.':
            continue

        # check if end statement came
        if endCame:
            line.setAddress(hex(currentAddress)[2:])
            continue
        if line.getCleanDirective() == "end":
            endCame = True

        if noStart:
            noStart = False
            adrressNotAssigned = True
            continue

        elif adrressNotAssigned:
            if line.getCleanDirective() == "start":
                startingAddress = int(line.getOperand(), 16)
                currentAddress = startingAddress
                adrressNotAssigned = False
            else:
                errorAddress = hex(int(errorAddress, 16) + 3)[2:]
                errorAddress = passTwo.fixHexString(errorAddress, 4)
                line.setAddress(errorAddress)
                # util.errorsTable["0000"] = ["missing or misplaced start statement"]
                adrressNotAssigned = True
                continue

        # if "start" put address as is
        if line.getCleanDirective() == "start":
            line.setAddress(hex(currentAddress)[2:])

        elif line.getCleanDirective() == "org":
            if line.getCleanOperand() != "":
                oldAddress = currentAddress

            if line.getCleanOperand().isdigit():
                currentAddress = int(line.getCleanOperand(), 16)
            elif line.getCleanOperand() == "":
                currentAddress = oldAddress
            elif line.getCleanOperand() in util.symTable.keys():
                currentAddress = int(util.symTable[line.getCleanOperand()][0], 16)
            continue

        else:
            line.setAddress(hex(currentAddress)[2:])

            # calculate reserved bytes and add to address
            if line.getCleanDirective() == "resb":
                currentAddress += int(line.getCleanOperand())
            # calculate reserved words(each of length 3) and add to address
            elif line.getCleanDirective() == "resw":
                currentAddress += 3 * int(line.getCleanOperand())
            # calculate length of string and add length to address
            elif line.getCleanDirective() == "byte":
                operand = line.getCleanOperand()[2:-1]
                if "c'" in line.getOperand().lower():
                    currentAddress += len(operand)
                elif "x'" in line.getOperand().lower():
                    currentAddress += len(operand) / 2
            # don't add to current address
            elif line.getCleanDirective() == "end":
                pass
            # don't add to current address but check expression
            elif line.getCleanDirective() == "equ":
                operand = line.getCleanOperand()
                equCounter += 1
                address = hex(currentAddress)[2:]

                if address not in util.errorsTable.keys():
                    util.errorsTable[address] = []

                if (not validExpression(line, operand, address, equCounter)):
                    util.errorsTable[address] += ["illegal expression", equCounter]
                    continue

            # normal address calculation
            else:
                currentAddress += 3

        address = line.getAddress()
        label = line.getCleanLabel()
        # if symbol not empty and not already present in symbol table and doesn't contain spaces, then add
        if (label != '') and (label not in util.symTable.keys()) and (' ' not in label):
            if (line.getCleanDirective() == "equ"):
                util.symTable[label] = [address, "a"]
            else:
                util.symTable[label] = [address, "r"]

    # update global list to be used later
    util.linesListWithData = linesList

def validExpression(line, operand, address, equCounter):
    regex = re.match("([-+]?[0-9]*?[0-9]+[\/\+\-\*])+([-+]?[0-9]*?[0-9]+)", operand)
    if regex is not None:  # sum of numbers
        return True

    line.setEqu(equCounter)
    tempOperand = operand
    valid = False
    noTerm = False

    terms = re.findall("([A-Za-z]+)([0-9]+)?", operand)
    i = 0
    for term in terms:
        terms[i] = term[0] + term[1]
        i += 1

    if (terms != []):
        for term in terms:
            if term not in util.symTable:
                util.errorsTable[address] += ["illegal operand field", equCounter]
                noTerm = True
            else:
                item = [term]
                for x in util.symTable[term]:
                    item.append(x)
                tempOperand = tempOperand.replace(term, item[2])

    for x in re.findall("([0-9]+)", tempOperand):
        tempOperand = tempOperand.replace(x, "a")

    while (len(tempOperand) >= 3) and (("a" in tempOperand) or ("r" in tempOperand)):
        reg1 = re.findall("r\s?-\s?r", tempOperand)[0] if re.findall("r\s?-\s?r", tempOperand) != [] else "k"
        tempOperand = tempOperand.replace(reg1, "a")
        reg2 = re.findall("a\s?\+\s?a", tempOperand)[0] if re.findall("a\s?\+\s?a", tempOperand) != [] else "k"
        tempOperand = tempOperand.replace(reg2, "a")
        reg3 = re.findall("a\s?-\s?a", tempOperand)[0] if re.findall("a\s?-\s?a", tempOperand) != [] else "k"
        tempOperand = tempOperand.replace(reg3, "a")

        if reg1 == reg2 == reg3 == "k":
            break

    if (not ((re.match("r\s?\+\s?r", tempOperand)) or
                 (re.match("r\s?\+\s?a", tempOperand)) or
                 (re.match("a\s?\+\s?r", tempOperand)))):
        valid = True
    else:
        valid = False

    if noTerm:
        valid = False

    # print "(", operand, "),(", tempOperand, "),", valid

    return valid
