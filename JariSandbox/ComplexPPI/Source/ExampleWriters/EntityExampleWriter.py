import sys
from SentenceExampleWriter import SentenceExampleWriter
import InteractionXML.IDUtils as IDUtils
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import cElementTree as ET

class EntityExampleWriter(SentenceExampleWriter):
    def __init__(self):
        self.xType = "token"
        self.insertWeights = False
    
    def writeXMLSentence(self, examples, predictionsByExample, sentenceObject, classSet, classIds, goldSentence=None):        
        self.assertSameSentence(examples)
        
        sentenceElement = sentenceObject.sentence
        sentenceId = sentenceElement.get("id")
        # detach analyses-element
        sentenceAnalysesElement = None
        sentenceAnalysesElement = sentenceElement.find("sentenceanalyses")
        if sentenceAnalysesElement != None:
            sentenceElement.remove(sentenceAnalysesElement)
        # remove pairs and interactions
        interactions = self.removeChildren(sentenceElement, ["pair", "interaction"])
        # remove entities
        newEntityIdCount = IDUtils.getNextFreeId(sentenceElement.findall("entity"))
        nonNameEntities = self.removeNonNameEntities(sentenceElement)
        
        # gold sentence elements
        goldEntityTypeByHeadOffset = {}
        goldEntityByHeadOffset = {}
        if goldSentence != None:
            for entity in goldSentence.entities:
                headOffset = entity.get("headOffset")
                if not goldEntityTypeByHeadOffset.has_key(headOffset):
                    goldEntityTypeByHeadOffset[headOffset] = []
                    goldEntityByHeadOffset[headOffset] = []
                goldEntityTypeByHeadOffset[headOffset].append(entity)
                goldEntityByHeadOffset[headOffset].append(entity)
            for key in goldEntityTypeByHeadOffset:
                goldEntityTypeByHeadOffset[key] =  self.getMergedEntityType(goldEntityTypeByHeadOffset[key])
            for token in sentenceObject.tokens:
                if not goldEntityTypeByHeadOffset.has_key(token.get("charOffset")):
                    goldEntityTypeByHeadOffset[token.get("charOffset")] = "neg"
            
        # add new pairs
        for example in examples:
            prediction = predictionsByExample[example[0]]
            entityElement = ET.Element("entity")
            entityElement.attrib["isName"] = "False"
            headToken = example[3]["t"]
            for token in sentenceObject.tokens:
                if token.get("id") == headToken:
                    headToken = token
                    break
            entityElement.attrib["charOffset"] = headToken.get("charOffset") 
            entityElement.attrib["headOffset"] = headToken.get("charOffset")
            entityElement.attrib["text"] = headToken.get("text")
            entityElement.attrib["id"] = sentenceId + ".e" + str(newEntityIdCount)
            self.setElementType(entityElement, prediction, classSet, classIds)
            if self.insertWeights: # in other words, use gold types
                headOffset = headToken.get("charOffset")
                if goldEntityByHeadOffset.has_key(headOffset):
                    for entity in goldEntityByHeadOffset[headOffset]:
                        entity.set("predictions", entityElement.get("predictions") )
            if goldEntityTypeByHeadOffset.has_key(headToken.get("charOffset")):
                entityElement.set("goldType", goldEntityTypeByHeadOffset[headToken.get("charOffset")])
            if (entityElement.get("type") != "neg" and not goldEntityByHeadOffset.has_key(entityElement.get("headOffset"))) or not self.insertWeights:
                newEntityIdCount += 1
                sentenceElement.append(entityElement)
        
        # if only adding weights, re-attach interactions and gold entities
        if self.insertWeights:
            for entity in nonNameEntities:
                sentenceElement.append(entity)
            for interaction in interactions:
                sentenceElement.append(interaction)

        # re-attach the analyses-element
        if sentenceAnalysesElement != None:
            sentenceElement.append(sentenceAnalysesElement)
    
    def getMergedEntityType(self, entities):
        """
        If a single token belongs to multiple entities of different types,
        a new, composite type is defined. This type is the alphabetically
        ordered types of these entities joined with '---'.
        """
        types = set()
        for entity in entities:
            types.add(entity.get("type"))
        types = list(types)
        types.sort()
        typeString = ""
        for type in types:
            if type == "Protein":
                continue
            if typeString != "":
                typeString += "---"
            typeString += type
        
        if typeString == "":
            return "neg"
        
        return typeString
