# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

import os
from dbDataAnalysisSqlite import cumulativeOccurrencesByReleaseYear, percentageOfOccurrenceByReleaseYear, totalMovies, search
from datetime import datetime

__author__ = "Justin Eyster"
__date__ = "$Jun 5, 2015 9:35:43 AM$"

def fileToStr(fileName): 
    """Return a string containing the contents of the an html file."""
    file = open(fileName); 
    contents = file.read();  
    file.close() 
    return contents

def generateSearchPage(defaultEarliestReleaseYear):
    """Generates the search page using inputPageTemplate and bootstrapThemeTemplate (html templates).
    Parameters: defaultEarliestReleaseYear - the earliest release year represented in the database.
    Returns: a string of html code representing the search page."""
    # define variables for the input page template
    numMovies = totalMovies()
    currentYear = str(datetime.now().year)
    # prepare page content, fill in the number of movies, and earliest and latest possible release years from above
    pageContent = fileToStr('templates/inputPageTemplate.html').format(**locals())

    # define other variables for the bootstrap template (this theme makes everything look pretty)
    # html code to activate the 'home' link, since we're on the home page
    homeActive = "class='active'"
    # the link of the home button is #, which is just a jump to the top of the current page (since already on home)
    homeLink = "#"
    # no nav bar, because we're on the search page, not the results page
    navBar = ""
    # ditto for graph
    graph = ""
    # fill in the bootstrap template with the pageContent, and the variables above
    return fileToStr('templates/bootstrapThemeTemplate.html').format(**locals())

def generateResultsPage(keywordOrPhrase, genre, earliestReleaseYear, latestReleaseYear, results, resultsPerPage, pageNumber):
    # initialize resultsPage variable
    resultsPage = ""
    # Later, place the following HTML code at the end of the results. (then put the nav bar after this.)
    resultsCap = "</a></div></body></html>"
    # variable to track oclc id of previous movie, to know if we need to start a new result or add to previous
    prevMovieOclcId = ""
    # iterate through results, use fillSearchResultsHTMLFile to generate HTML code for the results page
    for i in range((pageNumber-1)*resultsPerPage, pageNumber*resultsPerPage):
        # if there are enough results for one more on the page...
        if len(results) > i:
            movieOclcId = results[i][0]
            movieTitle = results[i][1]
            movieLineNumber = results[i][2]
            movieStartTimeStamp = results[i][3]
            movieEndTimeStamp = results[i][4]
            movieLineText = results[i][5]
            # if line is from a new movie...
            if prevMovieOclcId != movieOclcId:
                # cap the previous movie, use function below to generate HTML code for next movie's results
                resultsPage += resultsCap + fillSearchResultsHTMLFile(movieOclcId,movieTitle,movieLineNumber,movieStartTimeStamp,movieEndTimeStamp,movieLineText)
            # if line is from same movie as previous, add the additional line to the movie's results
            elif prevMovieOclcId == movieOclcId:
                resultsPage += fillAdditionalLinesHTMLFile(movieLineNumber,movieStartTimeStamp,movieEndTimeStamp,movieLineText)
            prevMovieOclcId = movieOclcId
    # as long as there are results...
    if len(results)>0:
        # message at top of page
        numResultsMessage = "<p class=message-text><a href='/moviesearch'>Back to search page.</a></p>" + \
                            "<p class=message-text>Showing " + str(len(results)) + " results for '" + keywordOrPhrase + \
                            "', " + str(resultsPerPage) + " per page.</p>" + \
                            "<p class=message-text>Click on a result to open the work's full script.</p>"

        # put together all the pieces into one final string of HTML code, with the results for the page and the
        # nav bar
        finalResult = numResultsMessage + resultsPage + resultsCap
        pageContent = finalResult
        homeActive = ""
        homeLink = "/moviesearch"
        # generate HTML code for the nav bar using the function below
        navBar = fillNavigationBarHTMLFile(keywordOrPhrase, genre, earliestReleaseYear, latestReleaseYear,
                                           pageNumber, len(results), resultsPerPage)
        if pageNumber == 1:
            graph = fillGraphHTMLFile(keywordOrPhrase, genre, earliestReleaseYear, latestReleaseYear,
                                      "percentageByReleaseYear")
        else:
            graph = ""
        return fileToStr('templates/bootstrapThemeTemplate.html').format(**locals())
    # if there are no results, say so
    else:
        return "Your Keyword/Phrase does not occur in the database (with specified parameters)."


def fillSearchResultsHTMLFile(oclcId, movieTitle, lineNumber, startTimeStamp, endTimeStamp, lineText):
    textFile = "/static/textFiles/" + str(oclcId) + ".txt"
    imageSource = "/static/imageFiles/" + str(oclcId) + ".gif"
    return fileToStr('templates/searchResultsTemplate.html').format(**locals())

def fillAdditionalLinesHTMLFile(lineNumber, startTimeStamp, endTimeStamp, lineText):
    return fileToStr('templates/additionalLinesFromSameMovieTemplate.html').format(**locals())

def fillGraphHTMLFile(keywordOrPhrase, genre, earliestReleaseYear, latestReleaseYear, plotType):
    if plotType == "percentageByReleaseYear":
        data = percentageOfOccurrenceByReleaseYear(keywordOrPhrase, genre, earliestReleaseYear, latestReleaseYear)
        twoDimensArrayOfVals = []
        for item in data:
            twoDimensArrayOfVals.append([item[0],item[1]])
        return fileToStr('templates/percentageAcrossReleaseYearGraphTemplate.html').format(**locals())


def fillNavigationBarHTMLFile(keywordOrPhrase, genre, earliestReleaseYear, latestReleaseYear, currentPageNum,
                              numResults, resultsPerPage):
    """
    Creates the HTML code for the pagination nav bar.
    :param keywordOrPhrase: the keyword/phrase searched by user
    :param currentPageNum: current page of results
    :param numResults: total number of results
    :param resultsPerPage: number of results to be displayed on each page
    :return: an HTML string for the pagination nav bar
    """
    # syntax to specify a page of results: '/moviesearch/<keywordOrPhrase>/<pageNumber:int>'

    # convert spaces to underscores in keyword/phrase (hyperlinks skip spaces)
    for i in range(len(keywordOrPhrase)):
        if keywordOrPhrase[i] == " ":
            keywordOrPhrase = keywordOrPhrase[0:i] + "_" + keywordOrPhrase[i+1:]

    # if we're on the first page of results
    if currentPageNum == 1:
        # don't include the jump to first button
        linkFirst = "#"
        # highlight the 1 on the nav bar
        active1 = "class='active'"
        # don't highlight the 2
        activeOther = ""
        # the first page shown on the nav bar will be 1
        pageNum1 = 1
        # decide if there's enough results to show 2, 3, 4, 5...else show 'N/A'
        if numResults > resultsPerPage:
            pageNum2 = 2
        else:
            pageNum2 = 'N/A'
        if numResults > resultsPerPage * 2:
            pageNum3 = 3
        else:
            pageNum3 = 'N/A'
        if numResults > resultsPerPage * 3:
            pageNum4 = 4
        else:
            pageNum4 = 'N/A'
        if numResults > resultsPerPage * 4:
            pageNum5 = 5
        else:
            pageNum5 = 'N/A'
    # if we're not on the first page of results
    else:
        # include the jump to first button
        linkFirst = "/moviesearch/" + keywordOrPhrase + "/" + genre + "/" + str(earliestReleaseYear) \
                      + "/" + str(latestReleaseYear) + "/" + "1"
        # don't highlight the first number on nav bar (it is for previous page)
        active1 = ""
        # highlight the second number on the nav bar (current page)
        activeOther = "class='active'"
        # first number on nav bar is for the previous page
        pageNum1 = currentPageNum - 1
        # second number on the nav bar is for the current page
        pageNum2 = currentPageNum
        # decide if there's enough results to show a next page, another page after that, and so on...
        # if not show 'N/A' in place of a page number
        if numResults > currentPageNum * resultsPerPage:
            pageNum3 = currentPageNum + 1
        else:
            pageNum3 = 'N/A'
        if numResults > (currentPageNum + 1) * resultsPerPage:
            pageNum4 = currentPageNum + 2
        else:
            pageNum4 = 'N/A'
        if numResults > (currentPageNum + 2) * resultsPerPage:
            pageNum5 = currentPageNum + 3
        else:
            pageNum5 = 'N/A'

    # set up 'Last Page' button
    lastPage = numResults // resultsPerPage
    if lastPage == 0:
        lastPage = 1
    if currentPageNum == lastPage:
        linkLast = "#"
        activeLast = "class='active'"
    else:
        linkLast = "/moviesearch/" + keywordOrPhrase + "/" + genre + "/" + str(earliestReleaseYear) \
                      + "/" + str(latestReleaseYear) + "/" + str(lastPage)
        activeLast = ""

    beginningOfNavUrls = '/moviesearch/'+keywordOrPhrase+'/'+genre+'/'+str(earliestReleaseYear)+'/'+str(latestReleaseYear)+'/'
    # when you click on the first number on the nav bar, it will go to either page 1 of results or the prev page
    link1 = beginningOfNavUrls + str(pageNum1)
    # for the second number on the nav bar, and third, and so on, decide if there are enough results to link
    # it to anything. If not, use '#' which jumps to top of current page.
    if pageNum2 != 'N/A':
        link2 = beginningOfNavUrls + str(pageNum2)
        button2 = "<li "+activeOther+"><a href='"+link2+"'>"+str(pageNum2)+"</a></li>"
    else:
        button2 = ""
    if pageNum3 != 'N/A':
        link3 = beginningOfNavUrls + str(pageNum3)
        button3 = "<li><a href='"+link3+"'>"+str(pageNum3)+"</a></li>"
    else:
        button3 = ""
    if pageNum4 != 'N/A':
        link4 = beginningOfNavUrls + str(pageNum4)
        button4 = "<li><a href='"+link4+"'>"+str(pageNum4)+"</a></li>"
    else:
        button4 = ""
    if pageNum5 != 'N/A':
        link5 = beginningOfNavUrls + str(pageNum5)
        button5 = "<li><a href='"+link5+"'>"+str(pageNum5)+"</a></li>"
    else:
        button5 = ""

    # if there are enough results to have a next page, link the next button to the next page, else use '#'
    # which jumpts to top of current page
    if numResults > currentPageNum * resultsPerPage:
        linkNext = beginningOfNavUrls + str(currentPageNum + 1)
    else:
        linkNext = '#'
    # if not on first page, the previous button should link to the previous page. If not use '#' which jumps to top
    # of current page
    if currentPageNum > 1:
        linkPrev = beginningOfNavUrls + str(currentPageNum - 1)
    else:
        linkPrev = '#'

    # return the string of HTML code for the nav bar
    return fileToStr('templates/navigationBarTemplate.html').format(**locals())