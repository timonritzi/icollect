from aiohttp import web
import aiohttp_cors
import shutil
from urllib.request import urlopen as uReq
from urllib.request import Request
import requests
from bs4 import BeautifulSoup as soup
import os
import ssl
import time
from secrets import token_hex
from urllib.parse import urlparse


# Create SessionID which is used as directory name
async def getSessionId(mPath):
    sessionId = token_hex(4)

    while os.path.isdir(os.path.join(mPath, sessionId)):
        sessionId = token_hex(4)

    return sessionId


# Parse URL with BeautifulSoup to HTML
async def makeSoup(url):

    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    uClient = uReq(req)
    page_html = uClient.read()

    page_soup = soup(page_html, "html.parser")

    return page_soup

# Parse with URLparser to get scheme & netloc to form the download URL
async def urlParser(url):

    parsed = urlparse(url)

    downloadUrl = f'{parsed.scheme}://{parsed.netloc}'

    return downloadUrl

# start of aiohttp handler
async def handle(request):
    data = await request.json()

    # Check if URL in request
    if 'url' not in data:
        resp = {
            'status': 'failed',
            'reason': 'missing Url'
        }

        return web.json_response(resp, status=403)

    url = data["url"]

    rootPath = '/tomin/backend'

    mediaPath = os.path.join(rootPath, 'media')

    # get sessionID
    sessionId = await getSessionId(mediaPath)

    # Join path to create directory
    sessionPath = os.path.join(mediaPath, sessionId)

    os.mkdir(sessionPath)

    # call HTML parser
    page_soup = await makeSoup(url)
    # call URL parser
    downloadUrl = await urlParser(url)

    # call main function
    await getMedia(page_soup, downloadUrl, sessionPath)

    # cd into media directory
    os.chdir(mediaPath)
    # create Zipfile from directory
    shutil.make_archive(f"{sessionId}", "zip", sessionId)
    # cd .. into root directory
    os.chdir(rootPath)

    resp = {
        'status': 'success',
        'sessionid': sessionId
    }

    return web.json_response(resp)


async def getMedia(page_soup, downloadUrl, sessionPath):
    imageSources = []

    extensions = ["jpg", "jpeg", "tif", "tiff", "gif", "png", "raw", "bmp", "eps", "svg"]

    # get all <img/> tags
    imgList = page_soup.find_all("img")

    # get all <div></div> tags
    divList = page_soup.find_all("div")

    # get all <iframe></iframe> tags
    iFrames = page_soup.find_all("iframe")

    # aList = page_soup.find_all("a")

    for frame in iFrames:

        link = frame.get("src")

        if "http" in link or "https" in link:

            # Parse new URL
            new_downloadUrl = await urlParser(link)

            # Parse new HTML
            new_soup = await makeSoup(link)

            # call main function with new Input
            await getMedia(new_soup, new_downloadUrl, sessionPath)

    # for a in aList:
    #
    #     link = a.get("href")
    #
    #     if "http" in link or "https" in link:
    #         # Parse new URL
    #         new_downloadUrl = await urlParser(link)
    #
    #         # Parse new HTML
    #         new_soup = await makeSoup(link)
    #
    #         # call main function with new Input
    #         await getMedia(new_soup, new_downloadUrl, sessionPath)

    for imgInDiv in divList:

        # get all Div's with data-thumbnail attribute
        attribute = imgInDiv.get("data-thumbnail")

        if attribute and attribute not in imageSources:
            imageSources.append(attribute)

    for imgElement in imgList:

        # get all src attributes
        imgSrc = imgElement.get('src')
        # get all data-src attributes
        imgAltSrc = imgElement.get('data-src')
        # get all srcset attributes
        imgSrcSet = imgElement.get('srcset')

        if imgSrc and imgSrc not in imageSources:
            imageSources.append(imgSrc)

        if imgAltSrc and imgAltSrc not in imageSources:
            imageSources.append(imgAltSrc)

        if imgSrcSet and imgSrcSet not in imageSources:
            imageSources.append(imgAltSrc)

    assetSources = []

    for assetSrc in imageSources:

        # create downloadUrl for each item in imageSources

        if assetSrc:

            if 'http://' in assetSrc or 'https://' in assetSrc:

                assetUrl = assetSrc

            elif downloadUrl not in assetSrc:

                if not assetSrc.startswith('/'):
                    assetSrc = '/' + assetSrc

                assetUrl = downloadUrl + assetSrc

            else:

                assetUrl = assetSrc

            if assetUrl not in assetSources:
                assetSources.append(assetUrl)

    for asset in assetSources:

        # download all images and save them to /media directory

        try:

            assetResponse = requests.get(asset)

            if assetResponse.status_code == 200:

                assetContent = assetResponse.content

                if assetContent:

                    assetExtension = asset.split(".")[-1]

                    if "?" in assetExtension:
                        assetExtension = assetExtension.split("?")[0]

                    if assetExtension.lower() in extensions:

                        assetName = token_hex(5) + "." + assetExtension

                        with open(os.path.join(sessionPath, assetName), 'wb') as f:

                            f.write(assetContent)

        except:

            print('Could not download file', asset)


app = web.Application()

app.add_routes([

    web.post('/', handle)

])

cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*"
    )
})

for route in list(app.router.routes()):
    cors.add(route)

ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_ctx.load_cert_chain(
    '/etc/letsencrypt/live/icollect.timonritzi.com/fullchain.pem',
    '/etc/letsencrypt/live/icollect.timonritzi.com/privkey.pem'
)

web.run_app(app, port=1337, ssl_context=ssl_ctx)


