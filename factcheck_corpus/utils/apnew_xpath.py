def apnews_xpath(selector, item):   
    if item=='articles':
        p1 = '//*[@id="root"]/div/main/div[3]/div/article/div/div/a/@href'
        urls = []
        for p in [p1]:
            if selector.xpath(p):
                urls = selector.xpath(p)
                break
        return urls
    
    if item=='pubdates':
        p1 = '//*[@id="root"]/div/main/div[3]/div/article/div/div/div/span[2]/text()'
        factcheckdates = ''
        for p in [p1]:
            if selector.xpath(p):
                factcheckdates = selector.xpath(p)
                break
        return factcheckdates

    if item=='authors':
        p1 = '//*[@id="root"]/div/main/div[3]/div/article/div/div/div/span[1]/text()'
        authors = ''
        for p in [p1]:
            if selector.xpath(p):
                authors = selector.xpath(p)
                break
        return authors

    if item=='body':
        p1 = '//*[@id="root"]/div/main/div[3]/div/div[6]/p//text()'
        p2 = '//*[@id="root"]/div/main/div[3]/div/div[7]/p//text()'
        body = ''
        for p in [p1, p2]:
            if selector.xpath(p):
                body = selector.xpath(p)
                break
        return body
    
    if item=='historical_pubdate':
        p1 = '//*[@id="root"]/div/main/div[3]/div/div[4]/div[2]/span[2]/text()'
        factcheckdate = ''
        for p in [p1]:
            if selector.xpath(p):
                factcheckdate = selector.xpath(p)
                break
        return factcheckdate
    
    if item=='historical_author':
        p1 = '//*[@id="root"]/div/main/div[3]/div/div[4]/div[2]/span[1]/text()'
        author = ''
        for p in [p1]:
            if selector.xpath(p):
                author = selector.xpath(p)
                break
        return author
    
    if item=='tags':
        p1 = '//*[@id="root"]/div/main/div[3]/div/div[3]/div/div[2]/ul//text()'
        tags = ''
        for p in [p1]:
            if selector.xpath(p):
                tags = selector.xpath(p)
                break
        # format: string list, e.g. ['Russia-Ukraine war', 'Kyiv'
        return tags 