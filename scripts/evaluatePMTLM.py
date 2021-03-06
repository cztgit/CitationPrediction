#!/usr/bin/python
import random
def getScore(d1Topics, d2Topics, etaVals):
    return sum([a*b*c for a,b,c in zip(d1Topics,d2Topics,etaVals)])

def getScoreDC(d1,d2,d1Topics, d2Topics, etaVals, dcParams):
    return dcParams[d1]*dcParams[d2]*sum([a*b*c for a,b,c in zip(d1Topics,d2Topics,etaVals)])

def main():
    global topicDists
    global etaVals
    global dcVals
    global numDocs
    global numTopics

    topicDists = []
    etaVals = []
    dcVals = []
    docnames = []

    corpus = 'acl_1000'
    pmtlm_vanilla = True
    approximateMaxNumRows = 2000
    text_suffix = ""
    if (pmtlm_vanilla is False):
        text_suffix = '-dc'
    thetaFile = '/Users/christanner/research/projects/CitationFinder/eval/pmtlm' + text_suffix + '/' + corpus +'/ThetaMatrix.txt'
    etaFile = '/Users/christanner/research/projects/CitationFinder/eval/pmtlm' + text_suffix + '/' + corpus + '/OmegaMatrix.txt'
    DCFile = '/Users/christanner/research/projects/CitationFinder/eval/pmtlm-dc/' + corpus + '/DCParams.txt'
    trainFile = '/Users/christanner/research/projects/CitationFinder/eval/' + corpus + '.training'
    testFile = '/Users/christanner/research/projects/CitationFinder/eval/' + corpus + '.testing'
    contentFile = '/Users/christanner/research/projects/CitationFinder/eval/' + corpus + '.content'
    outputScoresFile =  '/Users/christanner/research/projects/CitationFinder/eval/scores_pmtlm_' + corpus + '.txt'

    # reads in the .content file so that we know the ordering of docs; e.g.,
    # doc1 = 'p05-1381'; the ordering generated by PMTLM via .content
    i=0
    with open(contentFile) as f:
        for line in f:
            tokens = line.split()
            docnames.append(tokens[0])
            i += 1
    f.close()

    # reads in topic distributions per doc
    with open(thetaFile) as f:
        for line in f:
            tokens = line.split()
            results = map(float, tokens)
            topicDists.append(results)

    print "we have " + str(len(topicDists)) + " docs' topicDists"
    f.close()

    # reads in eta values (1 per topic)
    with open(etaFile) as f:
        for line in f:
            etaVals.append(float(line))
    f.close()

    # reads in degree-correcting vals (1 per doc)
    if (pmtlm_vanilla is False):
        minVal = 999
        with open(DCFile) as f:
            for line in f:
                if (float(line) < minVal and float(line) > 0):
                    minVal = float(line)
                #dcVals.append(float(line))
        f.close()
        print "min DC val: " + str(minVal)
        
        with open(DCFile) as f:
            for line in f:
                curVal = float(line)
                if curVal == 0:
                    curVal = minVal
                dcVals.append(curVal)

        # ensures files were legit
        if (len(dcVals) != len(topicDists)):
            print "dcVals file does not match w/ thetaFila!"
            exit(1)


    # reads in training's golden, so that we know to exclude these from our predicted links
    training = {}
    with open(trainFile) as f:
        for line in f:
            tokens = line.split()
            training.setdefault(tokens[1],list()).append(tokens[0])
    f.close()

    # reads in testing's golden
    testing = {}
    with open(testFile) as f:
        for line in f:
            tokens = line.split()
            testing.setdefault(tokens[1],list()).append(tokens[0])
    f.close()

    numDocs = len(topicDists)
    numTopics = len(etaVals)

    recalls = {}
    precisions = {}
    falsePositives = {}

    # my way of ranking (avg report performance)
    outScores = open(outputScoresFile, 'w')
    for report in docnames:
        if ((report in training.keys()) or (report in testing.keys())):
            for source in docnames:
                if (source != report):
                    d1Topics = topicDists[docnames.index(report)]
                    d2Topics = topicDists[docnames.index(source)]
                    score = 0
                    if (pmtlm_vanilla == True):
                        score = getScore(d1Topics, d2Topics, etaVals)
                    else:
                        score = getScoreDC(docnames.index(report),docnames.index(source),d1Topics, d2Topics, etaVals, dcVals)
                    outScores.write(report + " " + source + " " + str(score) + "\n")
    outScores.close()

    avgG1 = open('/Users/christanner/research/projects/CitationFinder/eval/avgG1-' + corpus + '-pmtlm' + text_suffix + '.csv', 'w')
    avgG2 = open('/Users/christanner/research/projects/CitationFinder/eval/avgG2-' + corpus + '-pmtlm' + text_suffix + '.csv', 'w')
    avgG3 = open('/Users/christanner/research/projects/CitationFinder/eval/avgG3-' + corpus + '-pmtlm' + text_suffix + '.csv', 'w')
    avgG1.write("recall,precision\n")
    avgG2.write("false_pos,true_pos\n")
    avgG3.write("#_returned,recall\n")
    for report in testing:
        trainTruth = training.get(report, list())
        d1Topics = topicDists[docnames.index(report)]

        curScores = {}
        #for i in range(0,numDocs):
        for doc in docnames:
            if (doc not in trainTruth and doc != report):
                d2Topics = topicDists[docnames.index(doc)]

                score = 0
                if (pmtlm_vanilla == True):
                    score = getScore(d1Topics, d2Topics, etaVals)
                else:
                    score = getScoreDC(docnames.index(report),docnames.index(doc),d1Topics, d2Topics, etaVals, dcVals)

                curScores[doc] = score

        totalPositiveToFind = len(testing[report])
        totalNegativeToFind = (len(curScores) - totalPositiveToFind)

        numReturned = 0
        numPositiveFound = 0
        numNegativeFound = 0
        # sort scores by value (for the given report)
        for source in sorted(curScores, key=curScores.get, reverse=True):
            numReturned += 1
            if (source in testing[report]):
                numPositiveFound += 1
            else:
                numNegativeFound += 1
            recall = float(numPositiveFound) / float(totalPositiveToFind)
            precision = float(numPositiveFound)  / float(numReturned)
            falsePos = float(numNegativeFound) / float(totalNegativeToFind)
            recalls.setdefault(numReturned,list()).append(recall)
            precisions.setdefault(numReturned,list()).append(precision)
            falsePositives.setdefault(numReturned,list()).append(falsePos)

    for i in sorted(recalls, key=recalls.get):
        recallAvg = sum(recalls[i]) / len(recalls[i])
        precAvg = sum(precisions[i]) / len(precisions[i])
        falsePosAvg = sum(falsePositives[i]) / len(falsePositives[i])
      
        avgG1.write(str(recallAvg) + "," + str(precAvg) + "\n")
        avgG2.write(str(falsePosAvg) + "," + str(recallAvg) + "\n")
        avgG3.write(str(i) + "," + str(recallAvg) + "\n")
    avgG1.close()
    avgG2.close()
    avgG3.close()
    outScores.close()

    recalls = {}
    precisions = {}
    falsePositives = {}
    # end of my approach of evaluating


    # evaluates the way that PMTLM does (1 global ranked list)
    # stores all rankings in 1 compressed list, which we'll rank by probability
    sourceProbs = {}
    totalPositiveToFind = 0
    totalNegativeToFind = 0
    for report in testing:

        trainTruth = training.get(report, list())
        d1Topics = topicDists[docnames.index(report)]

        numSources = 0
        #for i in range(0,numDocs):
        for doc in docnames:
            if (doc not in trainTruth and doc != report):
                d2Topics = topicDists[docnames.index(doc)]

                score = 0
                if (pmtlm_vanilla == True):
                    score = getScore(d1Topics, d2Topics, etaVals)
                else:
                    score = getScoreDC(docnames.index(report),docnames.index(doc),d1Topics, d2Topics, etaVals, dcVals)

                sourceProbs[report + "_" + doc] = score
                numSources += 1

        totalPositiveToFind += len(testing[report])
        totalNegativeToFind += (numSources - len(testing[report]))

        print str(report) + "\ttotal return: " + str(len(sourceProbs))

    # prints the data for our 2 graphs
    globalG1 = open('/Users/christanner/research/projects/CitationFinder/eval/globalG1-' + corpus + '-pmtlm' + text_suffix + '.csv', 'w')
    globalG2 = open('/Users/christanner/research/projects/CitationFinder/eval/globalG2-' + corpus + '-pmtlm' + text_suffix + '.csv', 'w')
    globalG1.write("recall,precision\n")
    globalG2.write("false_pos,true_pos\n")

    numReturned = 0
    numPositiveFound = 0
    numNegativeFound = 0

    rate = float(approximateMaxNumRows) / float(len(sourceProbs))

    for i in sorted(sourceProbs, key=sourceProbs.get, reverse=True):
        numReturned += 1
        tokens = i.split("_")
        d1 = tokens[0]
        d2 = tokens[1]

        if (d2 in testing[d1]):
            numPositiveFound += 1
        else:
            numNegativeFound += 1

        recall = float(numPositiveFound) / float(totalPositiveToFind)
        precision = float(numPositiveFound)  / float(numReturned)
        falsePos = float(numNegativeFound) / float(totalNegativeToFind)

        if random.random() < rate:
            globalG1.write(str(recall) + "," + str(precision) + "\n")
            globalG2.write(str(falsePos) + "," + str(recall) + "\n")

    globalG1.close()
    globalG2.close()
main()
