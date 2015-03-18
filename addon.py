import urllib,urllib2,urlparse
import xbmcplugin,xbmcgui,sys
import simplejson as json

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

xbmcplugin.setContent(addon_handle, 'movies')
video_res = [720,480,360,180][int(xbmcplugin.getSetting(addon_handle, 'video_res'))]

def build_url(query):
	return base_url + '?' + urllib.urlencode(query)

def build_folders(subcat_ary):
	for s in subcat_ary:
		url = build_url({'mode': s.get('key')})
		li = xbmcgui.ListItem(s.get('name'))
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
		if 'media' in s: build_media_entries(s['media'])

def build_media_entries(file_ary):
	for r in file_ary:
		if 'pnr' in r['images']: wide_img = r['images']['pnr'].get('md')
		else: wide_img = ''

		if 'sqr' in r['images']: img = r['images']['sqr'].get('md')
		else: img = ''

		li = xbmcgui.ListItem(r.get('title'))
		li.setIconImage(wide_img)
		li.setThumbnailImage(img)
		li.addStreamInfo('video', {'duration':r.get('duration')})
		li.setProperty('fanart_image', wide_img)
		video = sorted([x for x in r['files'] if x['frameHeight'] <= video_res], reverse=True)[0]
		xbmcplugin.addDirectoryItem(handle=addon_handle,
									url=video['progressiveDownloadURL'],
									listitem=li)

mode = args.get('mode', None)

if mode is None:
	cats_raw = urllib2.urlopen("http://mediator.jw.org/v1/categories/E?").read().decode("utf-8")
	categories = json.loads(cats_raw)

	for c in categories['categories']:
		url = build_url({'mode': c.get('key')})
		li = xbmcgui.ListItem(c.get('name'))
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

	xbmcplugin.endOfDirectory(addon_handle)

else:
	url = 'http://mediator.jw.org/v1/categories/E/' + mode[0] + '?&detailed=1'
	data = urllib2.urlopen(url).read().decode("utf-8")
	info = json.loads(data)
	if 'subcategories' in info['category']: build_folders(info['category']['subcategories'])
	if 'media' in info['category']: build_media_entries(info['category']['media'])

	xbmcplugin.endOfDirectory(addon_handle)
