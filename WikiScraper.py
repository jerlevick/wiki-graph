import requests
from bs4 import BeautifulSoup, Tag
import re
import networkx as nx
import json 

def find_sections(soup):
    """Finds sections in a BeautifulSoup object by searching for h2 headers
    
    Parameters
    -----------------
    soup : BeautifulSoup object
        A BS4 object representation of a Wikipedia page

    Returns
    ------------------
    sections : List
        A list of all the section headings of sections in the Wikipedia page
    """

    return [i.text for i in soup.find_all('h2')]

def go_to_section(soup, section):
    """Returns a BeautifulSoup object of the html of a particular section of a Wikipedia page
    
    Parameters
    -----------------
    soup : BeatifulSoup object
        A BS4 object representation of a Wikipedia page
    section : str
        The heading of a section on the page to be returned

    Returns
    -----------------
    A BeautifulSoup representation of the appropriate section of the Wikipedia page
    """

    if not section in find_sections(soup):
        return
    else:
        sec = [i for i in soup.find_all('h2') if i.text == section][0]
        sexn = str(sec)
        sec = sec.nextSibling
        while (not isinstance(sec, Tag) and not re.search(r'<h2>', str(sec))) or not sec.name == 'h2':
            sexn += str(sec)
            try:
                sec = sec.nextSibling
            except:
                break
        return BeautifulSoup(sexn,'html')
    
def extract_see_also(soup):
    """Gets the See Also section as a BeautifulSoup object from a particular BeautifulSoup object representing a 
    Wikipedia page
    
    Parameters 
    ----------------
    soup : BeautifulSoup object
        BS4 representation of a Wikipedia page

    Returns
    ----------------
    see_also : BeautifulSoup object
        BS4 representation of the "See Also" section of the Wikipedia page
    """

    sections = find_sections(soup)
    if (i in sections for i in ['See also', 'See Also']):
        see_also = [i for i in soup.find_all('h2') if i.text == 'See also'][0]
    while not isinstance(see_also, Tag) or not see_also.find_all('a'):
        see_also = see_also.nextSibling
    return see_also    

def find_see_also_notes(soup):
    """Find any other see also sections embedded in orther sections
    
    Parameters
    -----------------
    soup : BeautifulSoup object
        A BS4 representation of a Wikipedia page

    Returns
    -----------------
    ans : List
        A list of tuples of the form (title, link) where title is the title of any Wikipedia page appearing in a 
        "See Also" note throughout the text of an article, and link is the link to that Wikipedia page
    """
    notes = soup.find_all('div',{'role':'note'})
    see_alsos_ = [i for i in notes if any (j in i.text.strip() for j in ['See also', 'see also', 'See Also', 'See also:'])]
    ans = []
    for i in see_alsos_:
        for j in i.find_all('a'):
            try:
                ans.append((j.text, j['href']))
            except KeyError:
                pass
    return ans

def find_categories(soup):
    """Gets a list of the categories for a Wikipedia page
    
    Parameters 
    ---------------
    soup : BeautifulSoup object
        A BS4 representation of a Wikipedia page

    Returns 
    --------------
        A list of BS4 objects corresponding to the category links associated to the Wikipedia page
    """

    return soup.find_all('div',{'id':'mw-normal-catlinks'})

def get_cat_titles(soup):
    """Returns a list of all the categories on a Wikipedia page, input as  a BS4 object
    
    Parameters 
    --------------
    soup : BeautifulSoup object
        A BS4 representation of a Wikipedia page
    
    Returns
    --------------
        A list of strings, where each string is a category found from finding the categories corresponding to the 
        Wikipedia page
    """
    try:
        cats = find_categories(soup)[0]
        return[i.text for i in cats.find_all('a') if i.text != 'Categories']
    except IndexError:
        return []

def extract_title(soup):
    """Gets the title from the BS4 object of a Wikipedia page
    
    Parameters
    --------------
    soup : BeautifulSoup object
        A BS4 representation of a Wikipedia page

    Returns
    ---------------
    title : str
        The title of the Wikipedia page
    """
    return soup.find_all('head')[0].find_all('title')[0].text.split(' - ')[0]

def add_to_cat_dict(soup, category_dict):
    """Given a BS4 of a Wikipedia page, gets its Categories and adds them to a category dictionary
    
    Parameters 
    -----------------
    soup : BeautifulSoup object
        A BS4 representation of a Wikipedia page
    category_dict: Dict
        A dictionary whose keys are Wikipedia pages, and whose values are lists of the corresponding categories

    Returns
    ------------------
    None
        Modifies category_dict in-place to add the current page to the dictionary
    """
    title = extract_title(soup)
    if title not in category_dict:
        category_dict[title] = get_cat_titles(soup)

def add_to_link_dict(response, title_to_link_dict):
    """Adds the title as a key to a title-to-link dictionary, with the url as the value; the input is the 
    requests.get object for the url
    
    Parameters
    ----------------
    response : requests.get object
        The result of a request to a Wikipedia page
    title_to_link_dict : Dict
        A dict whose keys are Wikipedia page titles, and whose value is the corresponding link to that page

    Returns
    ----------------
    None
        Modifies title_to_link_dict in-place to add the current page to the dictionary

    """
    soup = BeautifulSoup(response.text)
    title = extract_title(soup)
    if title not in title_to_link_dict:
        title_to_link_dict[title] = response.url

def get_titles_and_links(section):
    """Section is a BS4 object, and this returns a list of tuples of the form (link text, link url) for all the 
    links in that section
    
    Parameters
    ---------------
    section : BeautifulSoup object
        A BS4 representation of a section of a Wikipedia page

    Returns
    --------------
    links : List
        A list whose entries are of the form (title, link) where title is the title of a Wikipedia page, and link
        is the link to that page, for all Wikipedia pages linked to from section
    """
    links = []
    for i in section.find_all('a'):
        if i.text != 'edit':
            try:
                links.append((i.text, i['href']))
            except KeyError:
                pass
    return links

def bfs_search(url, dictionaries, depth=3):
    """Starting at a given url, searches outward to a depth of depth and adds the linkage data to a dictionary
    
    Parameters
    ---------------
    url : str
        The url of a Wikipedia page
    
    dictionaries : List
        A list of dictionaries, graph_dict, text_to_link_dict, category_dict respectively, which comprise:
    
    graph_dict : Dict
        A dictionary represntation of the connectedness graph, whose keys are Wikipedia pages, and values are lists
        of all pages linked to from that page's "See Also" section

    text_to_link_dict : Dict
        Dictionary whose keys are Wikipedia page titles, and values are the associated link to that page
    
    category_dict : Dict
        Dictioanary whose keys are Wikipedia page titles, and values are lists of all the categories associated to 
        that page

    Depth : int
        The depth to which the breadth-first search should go

    Returns
    ----------------
    None
        Modifies the dictionaries in-place by adding all pages up to a distance of depth from url into the 
        dictionaries in the appropriate way
    """
    
    # Initialize the search by saying we have visited the start page, and the start page has a depth of 0
    visited = [url]
    queue = [(url, 0)]
    
    # Unpack the list of dictionaries into the three dictionaries we want
    graph_dict, text_to_link_dict, category_dict = dictionaries 

    while queue and not all(q[1] > depth for q in queue):
            
            curr_url, dist = queue.pop(-1) 
            response = requests.get('https://en.wikipedia.org/' + curr_url)
            soup = BeautifulSoup(response.text)
            add_to_link_dict(response, text_to_link_dict)
            add_to_cat_dict(soup, category_dict)

            if any('See also' in i for i in find_sections(soup)):
                j = ['See also' in i for i in find_sections(soup)].index(True)
                titles_and_links = get_titles_and_links(go_to_section(soup, find_sections(soup)[j]))
                also_titles_and_links = find_see_also_notes(soup)

                # Add to the dictionary
                if extract_title(soup) not in graph_dict:
                    graph_dict[extract_title(soup)] = [i[0] for i in titles_and_links] + [i[0] for i in also_titles_and_links]
                    for (title, link) in titles_and_links:
                        text_to_link_dict[title] = link
                    for (title, link) in also_titles_and_links:
                        text_to_link_dict[title] = link

                for (title, link) in titles_and_links + also_titles_and_links:
                    if link not in visited:
                        visited.append(link)
                        queue.insert(0, (link, dist + 1))