def factcheckorg_xpath(selector, item):
    if item=='articles':
        p1 = '//article/h3/a/@href'
        p2 = '//article/h3/a/@href'
        urls = []
        for p in [p1, p2]:
            if selector.xpath(p):
                urls = selector.xpath(p)
                break
        return urls
    
    if item=='pubdates':
        p1 = '//header/div/text()'
        p2 = '//header/div/text()'
        pubdates = []
        for p in [p1, p2]:
            if selector.xpath(p):
                pubdates = selector.xpath(p)
                break
        return pubdates
    
    if item=='fact':
        p1 = '//*[@id=\"content\"]/header/h1/text()'
        fact = []
        for p in [p1]:
            if selector.xpath(p):
                fact = selector.xpath(p)
                break
        if not fact: return ''
        else: return fact
    
    if item=='author':
        p1 = '//*[@id=\"content\"]/header/div[2]/p[1]/a/text()'
        author = ''
        for p in [p1]:
            if selector.xpath(p):
                author = selector.xpath(p)
                break
        return author
    
    if item=='review':
        p1 = '//article/div//p//text()'
        
        review = ''
        for p in [p1]:
            if selector.xpath(p):
                review = selector.xpath(p)
                break
        return review
    
    if item=='imageurl':
        p1 = '//article/div/div[1]/a/img/@src'
              
        imageurl = ''
        for p in [p1]:
            if selector.xpath(p):
                imageurl = selector.xpath(p)
                break
        return imageurl
    
    if item=='tags':
        p1 = "//footer/div/ul/li/ul/li//text()"
        
        tags = ''
        for p in [p1]:
            if selector.xpath(p):
                tags = selector.xpath(p)
                break
        tags = list(set([t for t in tags if t!='\n' and t!='\n\t']))
        return tags