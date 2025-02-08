def healthfeedback_xpath(selector, item):   
    if item=='articles':
        p1 = 'TODO:'
        urls = []
        for p in [p1]:
            if selector.xpath(p):
                urls = selector.xpath(p)
                break
        return urls
    
    if item=='pubdates':
        p1 = 'TODO:'
        factcheckdates = ''
        for p in [p1]:
            if selector.xpath(p):
                factcheckdates = selector.xpath(p)
                break
        return factcheckdates

    if item=='authors':
        p1 = 'TODO:'
        authors = ''
        for p in [p1]:
            if selector.xpath(p):
                authors = selector.xpath(p)
                break
        return authors

    if item=='body':
        p1 = 'TODO:'
        p2 = 'TODO:'
        body = ''
        for p in [p1, p2]:
            if selector.xpath(p):
                body = selector.xpath(p)
                break
        return body
    
    if item=='historical_pubdate':
        p1 = 'TODO:'
        factcheckdate = ''
        for p in [p1]:
            if selector.xpath(p):
                factcheckdate = selector.xpath(p)
                break
        return factcheckdate
    
    if item=='historical_author':
        p1 = 'TODO:'
        author = ''
        for p in [p1]:
            if selector.xpath(p):
                author = selector.xpath(p)
                break
        return author
    
    if item=='tags':
        p1 = 'TODO:'
        tags = ''
        for p in [p1]:
            if selector.xpath(p):
                tags = selector.xpath(p)
                break
        # format: string list, e.g. ['Russia-Ukraine war', 'Kyiv'
        return tags 