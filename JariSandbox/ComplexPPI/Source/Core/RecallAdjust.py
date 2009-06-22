try:
    import xml.etree.cElementTree as ET
except:
    import cElementTree as ET
import cElementTreeUtils as ETUtils
import math
from optparse import OptionParser
import sys

#Scales the value; works correctly for both positive and negative values
def scaleVal(val,boost=1.0):
    if val>=0: #non-negative case
        val*=boost
    else: #negative case (pretend as if it were positive, and translate back)
        diff=abs(val)*boost-abs(val)
        val+=diff
    return val

def adjustEntity(entityNode,targetLabel,multiplier):
    """Adjust the confidence of targetLabel in entityNode by multiplier"""
    predictions=entityNode.get("predictions")
    if not predictions: #nothing to do
        return
    labMod=[] #list with modified "label:confidence"
    for labelConfidence in predictions.split(","):
        label,confidence=labelConfidence.split(":")
        if label!=targetLabel: #nothing to do
            labMod.append(labelConfidence)
            continue
        else:
            confidence=scaleVal(float(confidence),multiplier) #modify...
            labMod.append(label+":"+str(confidence))
    #Done
    entityNode.set("predictions",",".join(labMod))

    

def recallAdjust(inFile,multiplier=1.0,outFile=None,targetLabel="neg"):
    """inFile can be a string with file name (.xml or .xml.gz) or an ElementTree or an Element or an open input stream
    multiplier adjusts the level of boosting the non-negative predictions, it is a real number (0,inf)
    multiplier 1.0 does nothing, <1.0 decreases negative class confidence, >1.0 increases negative class confidence
    the root of the modified tree is returned and, if outFile is a string, written out to outFile as well"""
    root=ETUtils.ETFromObj(inFile)
    if not ET.iselement(root):
        assert isinstance(root,ET.ElementTree)
        root=root.getroot()
    for entityNode in root.getiterator("entity"):
        adjustEntity(entityNode,targetLabel,multiplier)
    if outFile:
        ETUtils.write(root,outFile)
    return root

if __name__=="__main__":
    desc="Negative class adjustment in entity predictions. Reads from stdin, writes to stdout."
    parser = OptionParser(description=desc)
    parser.add_option("-l","--lambda",dest="l",action="store",default=None,type="float",help="The adjustment weight for the negative class. 1.0 does nothing, <1.0 decreases the predictions, >1.0 increases the predictions. No default.")
    parser.add_option("-t","--targetLabel",dest="targetLabel",action="store",default="neg",help="The label of the class to be adjusted. Defaults to 'neg'.")

    (options, args) = parser.parse_args()

    if options.l==None:
        print >> sys.stderr, "You need to give a lambda"
        sys.exit(1)

    recallAdjust(sys.stdin,options.l,sys.stdout,options.targetLabel)
