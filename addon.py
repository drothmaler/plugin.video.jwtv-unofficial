import urllib,urllib2,xbmcplugin,xbmcgui,sys
import simplejson as json

addon_handle = int(sys.argv[1])

xbmcplugin.setContent(addon_handle, 'movies')

url = 'http://mediator.jw.org/v1/categories/E/LatestVideos?&detailed=1'
data = urllib2.urlopen(url).read().decode("utf-8")
info = json.loads(data)
results = info['category']['media']

for r in results:
	li = xbmcgui.ListItem(r.get('title'), iconImage=r['images']['pnr'].get('md'))
	xbmcplugin.addDirectoryItem(handle=addon_handle, url=r['files'][-1].get('progressiveDownloadURL'), listitem=li)

xbmcplugin.endOfDirectory(addon_handle)
