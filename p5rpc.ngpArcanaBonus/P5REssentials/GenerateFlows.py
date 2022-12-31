from pathlib import Path
import re
import os
import shutil

# TODO Fix CORP002 no worky :(

scriptCompiler = "E:\\Programs\\AtlusScriptTools\\AtlusScriptCompiler.exe"
scrtipCompilerArgs = "-Compile -OutFormat V3BE -Library P5R -Encoding P5 -Hook"

# Takes a string and the index of something inside of a function then returns just the function with _hook appended to it
def MakeFunctionHook(text: str, startIndex: int, endIndex: int, varName: str, doneFunctions: list):
    openBrackets = [i for i, c in enumerate(text[:startIndex]) if c == '{']
    openBrackets.reverse()
    closeBrackets = [i for i, c in enumerate(text[startIndex:]) if c == '}']
    functions = [m.span() for m in re.finditer(r"void .*\(\)", text)]
    # print(f"Function indexes are {functions}")
    # print(f"Open bracket indexes are {openBrackets}")
    # print(f"Closed bracket indexes are {closeBrackets}")

    functionStartIndex = 0
    functionEndIndex = len(text) - 1

    # Find start of function
    for bracket in openBrackets:
        # If the bracket is the start of a function
        if bracket - 1 in [f[1] for f in functions]:
            functionStartIndex = [f[0]
                                  for f in functions if f[1] == bracket - 1][0]
            break

    # Change open brackets to be from the start to end
    openBrackets = [i for i, c in enumerate(text[startIndex:]) if c == '{']
    functions = [m.span() for m in re.finditer(
        r"void .*\(\)", text[startIndex:])]

    # print(f"Open bracket indexes are {openBrackets}")
    # print(f"Function indexes are {functions}")
    # print("Text is")
    # print(text[startIndex:])

    # Find end of function
    for i in range(len(closeBrackets)):
        # If the bracket is the start of a function
        if openBrackets[i] - 1 in [f[1] for f in functions]:
            # functionAfterIndex = [f
            #                  for f in functions if f[1] == openBrackets[i] - 1][0]
            # print(f"Function after is {text[startIndex:][functionAfterIndex[0]:functionAfterIndex[1]]}")
            # print(f"Close brackets is at {i}")
            functionEndIndex = closeBrackets[i] + startIndex + 1
            break

    function = text[functionStartIndex:functionEndIndex]
    endIndex = endIndex - functionStartIndex
    addition = """
            else
            {
                DispMaxItemMessage( {varName} );
            }
""".replace("{varName}", varName)
    function = function[:endIndex] + addition + function[endIndex + 1:]
    
    text = text[:functionStartIndex] + function + text[functionEndIndex:]

    # print("Function is")
    # print(function)
    functionNameSearch = re.search(r"(void )(.*)(\(\))", function)

    function = re.sub(r"(void )(.*)(\(\))",
                      r"\g<1>\g<2>_hook\g<3>", function) + "\n"

    if functionNameSearch is not None:
        functionName = functionNameSearch.group(2)
        existingFunctions = [x for x in doneFunctions if x[0] == functionName]
        if len(existingFunctions) > 0:
            doneFunctions = [x for x in doneFunctions if x[0] != functionName] + [(functionName, function)]
        else:
            doneFunctions = doneFunctions + [(functionName, function)]


    return (doneFunctions, text, len(addition))


def MakeFlows():
    for file in Path(unpackedPath).rglob("*.flow"):
        fileText = file.read_text('utf8')
        found = [(m.start(), m.end(), m.group(1)) for m in re.finditer(
            r"(?:else )?if \( CMM_CHK_ARCANA_PSSTOCKLV\( ([\w\d]+) \) != 0 \)\s*{.*?}", fileText, re.S)]
        if len(found) > 0:
            # print(found)
            doneFunctions = []
            flowPath = ".\\CPK\\MaxItemMessages\\" + \
                '\\'.join([str(x) for x in file.parts[4:-1]])
            if not os.path.exists(flowPath):
                os.makedirs(flowPath)

            flowPath = flowPath + "\\" + file.name.lower().replace(".bf.flow", ".flow").upper()
            flowPath = flowPath.upper()
            shutil.copyfile('\\'.join([str(x).upper() for x in file.parts]).replace(
                ".BF.FLOW", ".BF"), flowPath.replace(".FLOW", ".BF"))
            with open(flowPath, 'w') as f:
                fileName = file.name.lower().replace(".bf.flow", ".BF").upper()
                function = f"import(\"{fileName}\");\nimport(\"../../MaxItem.flow\");\n\n"
                offset = 0
                for item in found:
                    doneFunctions, fileText, newOffset = MakeFunctionHook(fileText,
                                                                  item[0] + offset, item[1] + offset, item[2], doneFunctions)
                    offset = offset + newOffset
                for doneFunction in doneFunctions:
                    function = function + doneFunction[1]
                f.write(function)
                print(f"Wrote hook for {flowPath}")

def CompileFlows():
    for file in Path(".\\CPK\\MaxItemMessages").rglob("*.FLOW"):
        os.system(
            f"{scriptCompiler} {file} {scrtipCompilerArgs} -Out \"{file.with_suffix('.FLOW.BF')}\"")
        bfFile = file.with_suffix('.BF')
        if bfFile.exists():
            os.remove(bfFile)
        file.with_suffix('.FLOW.BF').rename(bfFile)
        print(f"Compiled {file}")


unpackedPath = "E:\\Modding\\P5R\\EN"
MakeFlows()
CompileFlows()
