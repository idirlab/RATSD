def factcheckafp_xpath(selector, item):
    # done
    if item=='articles':
        p1 = '/html/body/main/div/a/@href'
        urls = []
        for p in [p1]:
            if selector.xpath(p):
                urls = selector.xpath(p)
                break
        return urls
    
    if item=='pubdates':
        p1 = '/html/body/main/div/a/div/div[2]/div/p/small/span[1]/text()'
        factcheckdate = ''
        for p in [p1]:
            if selector.xpath(p):
                factcheckdate = selector.xpath(p)
                break
        return factcheckdate
    
    if item=='summary':
        p1 = '/html/body/article/div[3]/h3[1]//text()'
        p2 = '/html/body/article/div[3]/p[1]//text()'
        summary = []
        for p in [p1]:
            if selector.xpath(p):
                summary = selector.xpath(p)
                break
        if not summary: return ''
        else: return summary
    
    if item=='review':
        p1 = '/html/body/article/div[3]/p//text()'
        review = ''
        for p in [p1]:
            if selector.xpath(p):
                review = selector.xpath(p)
                break
        return review
    
    if item=='imageurl':
        p1 = '/html/body/main/div/a/div/div[1]/img/@src'
        imageurl = ''
        for p in [p1]:
            if selector.xpath(p):
                imageurl = selector.xpath(p)
                break
        return imageurl

    if item=='tags':
        p1 = '/html/body/div[6]/div[2]/a/text()'
        p2 = '/html/body/div[6]/div[3]/a/text()'
        tags = ''
        for p in [p1, p2]:
            if selector.xpath(p):
                tags = selector.xpath(p)
                break
        return tags