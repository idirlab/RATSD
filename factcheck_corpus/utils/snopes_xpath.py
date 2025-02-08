def snopes_xpath(selector, item):
    if item=='articles':
        p1 = "/html/body/div[3]/div/div[1]/main/div[2]/div/article/a/@href"
        p2 = '/html/body/div[4]/div/div[1]/main/div[2]/div/article/a/@href'
        urls = []
        for p in [p1, p2]:
            if selector.xpath(p):
                urls = selector.xpath(p)
                break
        return urls
    
    if item=='claim':
        p1 = '/html/body/div[4]/div/div[1]/main/article/div[2]/div[2]/text()'
        p2 = '/html/body/div[4]/div/div[1]/main/article/div[2]/p[1]/text()'
        p3 = '/html/body/div[4]/div/div[1]/main/article/div[2]/p[2]/text()'
        p4 = '/html/body/div[4]/div/div[1]/main/article/div[2]/div/div/p[1]/text()'
        p5 = '/html/body/div[4]/div/div[1]/main/article/div[2]/div/p[3]/text()'
        p6 = '/html/body/div[4]/div/div[1]/main/article/div[2]/div/p[2]/text()'
        p7 = '/html/body/div[4]/div/div[1]/main/article/div[2]/div/p[4]/text()'
        p8 = '/html/body/div[4]/div/div[1]/main/article/div[2]/p[2]/span/text()'
        p9 = '/html/body/div[4]/div/div[1]/main/article/div[2]/div[1]/p[2]/text()'
        claim = []
        for p in [p1, p2 ,p3 ,p4, p5, p6, p7, p8, p9]:
            if selector.xpath(p):
                claim = selector.xpath(p)
                break
        return claim
    
    if item=='verdict':
        p1 = '/html/body/div[4]/div/div[1]/main/article/div[3]/div[2]/div/div[2]/span/text()'
        p2 = '/html/body/div[4]/div/div[1]/main/article/div[2]/div[2]/div/div[2]/span/text()'
        p3 = '/html/body/div[4]/div/div[1]/main/article/div[4]/div[2]/div/div[2]/span/text()'
        p4 = '/html/body/div[4]/div/div[1]/main/article/div[3]/div[3]/div[2]/div/div[2]/span/text()'
        p5 = '/html/body/div[4]/div/div[1]/main/article/div[2]/div[1]/span/text()'
        p6 = '/html/body/div[4]/div/div[1]/main/article/div[2]/div[2]/span/text()'
        p7 = '/html/body/div[4]/div/div[1]/main/article/div[2]/div/div/div[1]/span/text()'
        p8 = '/html/body/div[4]/div/div[1]/main/article/div[2]/p[3]/span/span/text()'
        p9 = '/html/body/div[4]/div/div[1]/main/article/div[2]/div/p[4]/span/span/text()'
        p10 = '/html/body/div[4]/div/div[1]/main/article/div[2]/div/p[4]/span/text()'
        p11 = '/html/body/div[4]/div/div[1]/main/article/div[2]/div/p[3]/span/span/text()'
        p12 = '/html/body/div[4]/div/div[1]/main/article/div[2]/div/p[4]/noindex/span/span/text()'
        verdict = []
        for p in [p1, p2 ,p3 ,p4, p5, p6, p7, p8, p9, p10, p11, p12]:
            if selector.xpath(p):
                verdict = selector.xpath(p)
                break
        if not verdict: return ''
        else: return verdict
    
    if item=='author':
        p1 = '/html/body/div[4]/div/div[1]/main/article/header/ul[1]/li/a/text()'
        p2 = '/html/body/div[4]/div/div[1]/main/article/header/ul[1]/li/span/text()'
        author = ''
        for p in [p1, p2]:
            if selector.xpath(p):
                author = selector.xpath(p)
                break
        return author
    
    if item=='date':
        p1 = '/html/body/div[4]/div/div[1]/main/article/header/ul[2]/li/time/text()'
        date = ''
        for p in [p1]:
            if selector.xpath(p):
                date = selector.xpath(p)
                break
        return date
    
    if item=='summary':
        # what's true about the claim
        p1 = '/html/body/div[4]/div/div[1]/main/article/div[3]/div[3]/div/div/p/text()'
        # what's false about the claim
        p2 = '/html/body/div[4]/div/div[1]/main/article/div[3]/div[4]/div/div/p/text()'
        
        p1_text = ''
        for p in [p1]:
            if selector.xpath(p):
                p1_text = selector.xpath(p)
                break
        if p1_text: p1_text = p1_text[0]
            
        p2_text = ''
        for p in [p2]:
            if selector.xpath(p):
                p2_text = selector.xpath(p)
                break
        if p2_text: p2_text = p2_text[0]
        
        if not p1_text and not p2_text: return ''
        else: return " ".join([p1_text, p2_text])
    
    if item=='review':
        p1 = '/html/body/div[4]/div/div[1]/main/article/div[6]/p//text()'
        p2 = '/html/body/div[4]/div/div[1]/main/article/div[5]/p//text()'
        p3 = '/html/body/div[4]/div/div[1]/main/article/div[5]/p//text()'
        p4 = '/html/body/div[4]/div/div[1]/main/article/div[7]/p//text()'
        p5 = '/html/body/div[4]/div/div[1]/main/article/div[3]/div[2]//text()'
        p6 = '/html/body/div[4]/div/div[1]/main/article/div[2]/p//text()'
        p7 = '/html/body/div[4]/div/div[1]/main/article/div[2]/div/div/p//text()'
        p8 = '/html/body/div[4]/div/div[1]/main/article/div[2]/div/p//text()'
        p9 = '/html/body/div[4]/div/div[1]/main/article/div[4]/p//text()'
        
        review = ''
        for p in [p1, p2 ,p3 ,p4, p5, p6, p7, p8, p9]:
            if selector.xpath(p):
                review = selector.xpath(p)
                break
        return review
    
    if item=='imageurl':
        p1 = '/html/body/div[4]/div/div[1]/main/article/header/figure/div/img/@src'
        p2 = '/html/body/div[4]/div/div[1]/main/article/header/figure/div/img/@data-lazy-src'    
              
        imageurl = ''
        for p in [p1, p2]:
            if selector.xpath(p):
                imageurl = selector.xpath(p)
                break
        return imageurl

    if item=='tags':
        p1 = '/html/body/div[4]/div/div[1]/main/article/nav/div[3]/a/text()'
        tags = ''
        for p in [p1]:
            if selector.xpath(p):
                tags = selector.xpath(p)
                break
        return tags
    