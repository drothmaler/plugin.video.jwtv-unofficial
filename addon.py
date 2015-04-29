import urllib,urllib2,urlparse
import xbmcplugin,xbmcgui,sys
import simplejson as json

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

xbmcplugin.setContent(addon_handle, 'movies')
vres = xbmcplugin.getSetting(addon_handle, 'video_res')
if vres not in ['0','1','2','3']: vres = '0'
video_res = [720,480,360,180][int(vres)]

def build_url(query):
	return base_url + '?' + urllib.urlencode(query)

def build_folders(subcat_ary):
	isStreaming = mode[0] == 'Streaming'
	for s in subcat_ary:
		url = build_url({'mode': s.get('key')})
		li = xbmcgui.ListItem(s.get('name'))
		if 'rph' in s['images']:
			li.setIconImage(s['images']['rph'].get('md'))
			li.setThumbnailImage(s['images']['rph'].get('md'))
		if 'pnr' in s['images']:
			li.setProperty('fanart_image', s['images']['pnr'].get('md'))
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=(isStreaming == False))

def get_video_metadata(file_ary):
	videoFiles = []
	for r in file_ary:
		sqr_img = ''
		wide_img = ''
		if 'sqr' in r['images']: sqr_img = r['images']['sqr'].get('md')
		elif 'cvr' in r['images']: sqr_img = r['images']['cvr'].get('md')
		if 'pnr' in r['images']: wide_img = r['images']['pnr'].get('md')
		video = sorted([x for x in r['files'] if x['frameHeight'] <= video_res], reverse=True)[0]
		videoFiles.append({'id':r['_id'],'video':video['progressiveDownloadURL'],'wide_img':wide_img,'sqr_img':sqr_img,'title':r.get('title'),'dur':r.get('duration')})
	return videoFiles

def build_media_entries(file_ary):
	for v in get_video_metadata(file_ary):
		li = xbmcgui.ListItem(v['title'])
		li.setIconImage(v['wide_img'])
		li.setThumbnailImage(v['sqr_img'])
		li.addStreamInfo('video', {'duration':v['dur']})
		li.setProperty('fanart_image', v['wide_img'])

		bingeAction = 'XBMC.RunPlugin(' + build_url({'mode':'watch_from_here','from_mode':mode[0],'first':v['id']}) + ')'
		li.addContextMenuItems([('Watch All Starting Here', bingeAction)], replaceItems=True)
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=v['video'], listitem=li)

def process_top_level():
	cats_raw = urllib2.urlopen("http://mediator.jw.org/v1/categories/E?").read().decode("utf-8")
	categories = json.loads(cats_raw)

	for c in categories['categories']:
		url = build_url({'mode': c.get('key')})
		li = xbmcgui.ListItem(c.get('name'))
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

	xbmcplugin.endOfDirectory(addon_handle)

def build_playlist(file_ary, first):
	added = 0
	current = float(0)
	foundStartEp = False

	metadata = get_video_metadata(file_ary)
	total = float(len(metadata))

	dl = xbmcgui.DialogProgress()
	dl.create('Watch Multiple', 'Queueing videos...')

	pl = xbmc.PlayList(1)
	pl.clear()

	for item in reversed(metadata):
		dl.update(int(current / total * 100))
		if item['id'] == first: foundStartEp = True
		if foundStartEp == True:
			added += 1
			li = xbmcgui.ListItem(item['title'], iconImage=item['sqr_img'])
			li.setThumbnailImage(item['sqr_img'])
			pl.add(item['video'], li)
		current += 1.0
	dl.close()

	if added > 0:
		xbmc.Player().play(pl)
	else:
		xbmcgui.Dialog().ok(" Problem ", " None of the videos are available. ")
	return pl

def process_sub_level(sub_level, create_playlist, from_id):
	url = 'http://mediator.jw.org/v1/categories/E/' + sub_level + '?&detailed=1'
	data = urllib2.urlopen(url).read().decode("utf-8")
	info = json.loads(data)
	if create_playlist == False:
		if 'subcategories' in info['category']: build_folders(info['category']['subcategories'])
		if 'media' in info['category']: build_media_entries(info['category']['media'])
		xbmcplugin.endOfDirectory(addon_handle)
	else:
		pl = build_playlist(info['category']['media'], from_id)
		xbmc.Player().play(pl)

def process_streaming():
	url = 'http://mediator.jw.org/v1/schedules/E/Streaming'
	data = urllib2.urlopen(url).read().decode("utf-8")
	info = json.loads(data)
	for s in info['category']['subcategories']:
		if s['key'] == mode[0]:
			pl = xbmc.PlayList(1)
			pl.clear()
			for item in get_video_metadata(s['media']):
				li = xbmcgui.ListItem(item['title'], iconImage=item['sqr_img'])
				li.setThumbnailImage(item['sqr_img'])
				pl.add(item['video'], li)
			xbmc.Player().play(pl)
			xbmc.Player().seekTime(s['position']['time'])
			return

mode = args.get('mode', None)

if mode is None: process_top_level()
elif mode[0] == 'watch_from_here': process_sub_level(args.get('from_mode')[0], True, args.get('first')[0])
elif (mode[0].startswith('Streaming') and len(mode[0]) > 9): process_streaming()
else: process_sub_level(mode[0], False, 0)
