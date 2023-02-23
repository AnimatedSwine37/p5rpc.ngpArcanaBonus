from pathlib import Path
import re
import os
import shutil

# TODO Fix CORP002 no worky :(

scriptCompiler = "E:\\Programs\\AtlusScriptTools\\AtlusScriptCompiler.exe"
scrtipCompilerArgs = "-Compile -OutFormat V3BE -Library P5R -Encoding P5 -Hook"

# Takes a string and the index of something inside of a function then returns just the function with _hook appended to it
def MakeFunctionHook(text: str, startIndex: int, endIndex: int, varName: str, doneFunctions: list):
    functions = [m.span() for m in re.finditer(r"void .*\(\)", text)]

    functionStartIndex = 0
    functionEndIndex = len(text) - 1

    startMatch = [m for m in re.finditer(r"^void .*\s{", text[:startIndex], re.M)][-1]
    functionStartIndex = startMatch.start()

    endMatch = [m for m in re.finditer(r"^}", text[startIndex:], re.M)][0]
    functionEndIndex = endMatch.start() + startIndex + 1

    function = text[functionStartIndex:functionEndIndex]
    endIndex = endIndex - functionStartIndex + 1
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
            doneFunctions = [x for x in doneFunctions if x[0]
                             != functionName] + [(functionName, function)]
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
