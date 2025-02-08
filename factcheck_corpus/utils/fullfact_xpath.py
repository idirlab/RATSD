def fullfact_xpath(selector, item):
    if item=='articles':
        p1 = '/html/body/main/div/div/div/div[1]/div/a/@href'
        urls = []
        for p in [p1]:
            if selector.xpath(p):
                urls = selector.xpath(p)
                break
        return urls
    
    if item=='claim':
        p1 = '/html/body/main/div/div/section[1]/article/div[2]/div/div[2]/div[1]/div/p//text()'
        claim = ''
        for p in [p1]:
            if selector.xpath(p):
                claim = selector.xpath(p)
                break
        return claim
    
    if item=='factcheckdate':
        p1 = '/html/body/main/div/div/section[1]/article/div[1]/text()'
        factcheckdate = ''
        for p in [p1]:
            if selector.xpath(p):
                factcheckdate = selector.xpath(p)
                break
        return factcheckdate
    
    if item=='summary':
        p1 = '/html/body/main/div/div/section[1]/article/div[2]/div/div[2]/div[2]/div/p//text()'
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
        p1 = '/html/body/main/div/div/section[1]/article/div[3]/p//text()'
        p2 = '/html/body/main/div/div/section[1]/article/p//text()'
        
        review = ''
        for p in [p1, p2]:
            if selector.xpath(p):
                review = selector.xpath(p)
                break
        return review
    
    if item=='imageurl':
        p1 = '/html/body/main/div/div/div/div[2]/img/@src'
              
        imageurl = ''
        for p in [p1]:
            if selector.xpath(p):
                imageurl = selector.xpath(p)
                break
        return imageurl

    if item=='tags':
        p1 = '/html/body/main/div/div/section[1]/nav/ol/li//text()'
              
        tags = ''
        for p in [p1]:
            if selector.xpath(p):
                tags = selector.xpath(p)
                break
        return tags
    


    