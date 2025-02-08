def politifact_xpath(selector, item):
    """
    tags: "HEALTH CHECK", "PUBLIC HEALTH", "DRUGS"
    """
    # check if any data in this page
    if item=='data':
        p1 = '//*[@id="top"]/main/section[3]/article/section/div/article/ul/li/article/div[1]/div[2]/a/text()' # author
        p2 = '//*[@id="top"]/main/section[3]/article/section/div/article/ul/li/article/div[2]/div/div[1]/div/a/text()' # claim
        p3 = '//*[@id="top"]/main/section[3]/article/section/div/article/ul/li/article/div[1]/div[2]/div/text()' # fact date
        p4 = '//*[@id="top"]/main/section[3]/article/section/div/article/ul/li/article/div[2]/div/footer/text()' # fact check date
        p5 = '//*[@id="top"]/main/section[3]/article/section/div/article/ul/li/article/div[2]/div/div[2]/div/picture/img/@alt' # verdict
        p6 = '//*[@id="top"]/main/section[3]/article/section/div/article/ul/li/article/div[2]/div/div[1]/div/a/@href' # url
        data = [selector.xpath(p) for p in [p1, p2, p3, p4, p5, p6]]
        if not any(data): return False
        else: return data
    
    if item=='review':
        p1 = '//*[@id="top"]/main/section[5]/div[2]/article//p//text()'
        p2 = '//*[@id="top"]/main/section[5]/div[2]/article//div//div//text()'
        p3 = '//*[@id="top"]/main/section[5]/div[2]/article/div//text()'
        p4 = '//*[@id="top"]/main/section[4]/div[2]/article/p//text()'
        p5 = '//*[@id="top"]/main/section[4]/div[2]/article//div//p//text()'
        p6 = '//*[@id="top"]/main/section[4]/div[2]/article//div//text()'
        p7 = '//*[@id="top"]/main/section[4]/div[2]/article//div//div//text()'
        review = []
        for p in [p1, p2 ,p3 ,p4, p5, p6, p7]:
            if selector.xpath(p):
                review = selector.xpath(p)
                break
        if not review: return ''
        else: return review
        
    if item=='summary':
        p1 = '//*[@id="top"]/main/section[5]/div[2]/header/h2/text()'
        p2 = '//*[@id="top"]/main/section[4]/div[2]/header/h2/text()'
        summary1 = ''
        for p in [p1, p2]:
            if selector.xpath(p):
                summary1 = selector.xpath(p)
                break
        # remove \n and questions
        if summary1: 
            summary1 = summary1[0].replace('\n', '')
            if summary1[-1] not in ["?", "."]: summary1 += '.' # add period to summary1
        else: summary1 = ''
        
        # summary2 refers to "If you time is short"
        p1 = '//*[@id="top"]/main/section[5]/div[2]/div[1]/div[1]/div/ul/li//text()'
        p2 = '/html/body/div[2]/main/section[4]/div[2]/div[1]/div[1]/div/ul/li//text()'
        p3 = '//*[@id="top"]/main/section[5]/div[2]/div[1]/div[1]/div/p//text()'
        p4 = '/html/body/div[2]/main/section[4]/div[2]/div[1]/div[1]/div/p//text()'
        summary2 = ''
        for p in [p1, p2, p3, p4]:
            if selector.xpath(p):
                summary2 = selector.xpath(p)
                break
            
        if summary2: summary2 = ' '.join(summary2).replace('\n', ' ').split('•')
        else: summary2 = ''
        
        fact = summary1+' '+''.join(summary2)
        return fact.lstrip().rstrip()
    
    if item=='imageurl':
        p1 = '//*[@id="top"]/main/section[4]/div[2]/section/article/div[1]/picture/source[1]/@srcset'              
        imageurl = ''
        for p in [p1]:
            if selector.xpath(p):
                imageurl = selector.xpath(p)
                break
        return imageurl
    
    if item=='tags':
        p1 = '//*[@id="top"]/main/section[3]/div/article/div[2]/div/ul/li/a/span/text()'
        tags = ''
        for p in [p1]:
            if selector.xpath(p):
                tags = selector.xpath(p)
                break
        return tags