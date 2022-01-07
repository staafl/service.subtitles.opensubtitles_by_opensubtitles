# -*- coding: utf-8 -*-

import os
import shutil
import sys
import urllib
import xbmc
import xbmcaddon
import xbmcgui,xbmcplugin
import xbmcvfs
import uuid
import json
import pysubs2
import chardet

__addon__ = xbmcaddon.Addon()
__author__     = __addon__.getAddonInfo('author')
__scriptid__   = __addon__.getAddonInfo('id')
__scriptname__ = __addon__.getAddonInfo('name')
__version__    = __addon__.getAddonInfo('version')
__language__   = __addon__.getLocalizedString

__cwd__        = xbmc.translatePath( __addon__.getAddonInfo('path') )
__profile__    = xbmc.translatePath( __addon__.getAddonInfo('profile') )
__resource__   = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) )
__temp__       = xbmc.translatePath( os.path.join( __profile__, 'temp', '') )

if xbmcvfs.exists(__temp__):
  shutil.rmtree(__temp__)
xbmcvfs.mkdirs(__temp__)

sys.path.append (__resource__)

from OSUtilities import OSDBServer, log, hashFile, normalizeString
from urllib.parse import unquote

def Search( item ):
  search_data = []
  try:
    search_data = OSDBServer().searchsubtitles(item)
  except:
    log( __name__, "failed to connect to service for subtitle search")
    xbmc.executebuiltin((u'Notification(%s,%s)' % (__scriptname__ , __language__(32001))))
    return

  if search_data != None:
    search_data.sort(key=lambda x: [x['LanguageName'], x['SubFileName']])
    listitems=[]
    listitems.append(xbmcgui.ListItem(label = "Local File..."))
    for item_data in search_data:
      ## hack to work around issue where Brazilian is not found as language in XBMC
      if item_data["LanguageName"] == "Brazilian":
        item_data["LanguageName"] = "Portuguese (Brazil)"

      if ((item['season'] == item_data['SeriesSeason'] and
          item['episode'] == item_data['SeriesEpisode']) or
          (item['season'] == "" and item['episode'] == "") ## for file search, season and episode == ""
         ):
        listitem = xbmcgui.ListItem(label          = item_data["LanguageName"],
                                    label2         = item_data["SubFileName"]
                                    )
        listitem.setArt( { "icon": str(int(round(float(item_data["SubRating"])/2))), "thumb" : item_data["ISO639"] } )
        listitem.setProperty( "sync", ("false", "true")[str(item_data["MatchedBy"]) == "moviehash"] )
        listitem.setProperty( "hearing_imp", ("false", "true")[int(item_data["SubHearingImpaired"]) != 0] )
        url = "plugin://%s/?action=download&link=%s&ID=%s&filename=%s&format=%s" % (__scriptid__,
                                                                          item_data["ZipDownloadLink"],
                                                                          item_data["IDSubtitleFile"],
                                                                          item_data["SubFileName"],
                                                                          item_data["SubFormat"]
                                                                          )
        listitems.append(listitem)
        if(__addon__.getSetting('dualsub_enable') != 'true'):
          xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=listitem,isFolder=False)
    if(__addon__.getSetting('dualsub_enable') == 'true'):
      subs=[]

      dialog = xbmcgui.Dialog()
      json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "xbmc.GetInfoLabels", "params":{"labels": ["player.FolderPath"]}, "id": 1}' )
      file_playing = json.loads(json_query).get('result').get('player.FolderPath')

      sub = dialog.select("Choose bottom subtitle", [i for i in listitems],useDetails=True)
      if sub > -1:

        if sub == 0:
          file = dialog.browse(1, "Choose Subtitle File ", "*", defaultt = file_playing)
          if not file:
            return
          offset = dialog.numeric(0, "Bottom subtitle offset x100ms", "0")
          if offset is None or offset == "":
              offset = "0"

          offset = int(offset)

          subs.append({'local': True,
            'offset':offset,
            'path': file
          })
        else:
          sub -= 1
          offset = dialog.numeric(0, "Bottom subtitle offset x100ms", "0")
          if offset is None or offset == "":
              offset = "0"

          offset = int(offset)

          subs.append({'ID':search_data[sub]['IDSubtitleFile'],
            'link':search_data[sub]['ZipDownloadLink'],
            'filename':search_data[sub]['SubFileName'],
            'format':search_data[sub]['SubFormat'],
            'offset':offset,
            'local': False})
        sub = dialog.select("Choose top subtitle", [i for i in listitems],useDetails=True)
        if sub > -1:

          if sub == 0:
            file = dialog.browse(1, "Choose Subtitle File ", "*", defaultt = file_playing)

            if not file:
              return
            offset = dialog.numeric(0, "Top subtitle offset in x100ms", "0")
            if offset is None or offset == "":
                offset = "0"

            offset = int(offset)

            subs.append({'local': True,
              'offset':offset,
              'path': file
            })
          else:
            offset = dialog.numeric(0, "Top subtitle offset in x100ms", "0")
            if offset is None or offset == "":
                offset = "0"

            offset = int(offset)

            sub -= 1
            subs.append({'ID':search_data[sub]['IDSubtitleFile'],
              'link':search_data[sub]['ZipDownloadLink'],
              'filename':search_data[sub]['SubFileName'],
              'format':search_data[sub]['SubFormat'],
              'offset':offset,
              'local': False})
          payload=json.dumps(subs[:2])
          payload=urllib.parse.quote(payload)
          listitem = xbmcgui.ListItem(label2=__language__(32019))
          url = "plugin://%s/?action=download&payload=%s"% (__scriptid__,payload)
          xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=listitem,isFolder=False)

def Download(id,url,format,stack=False):
  subtitle_list = []
  exts = [".srt", ".sub", ".txt", ".smi", ".ssa", ".ass" ]
  if stack:         ## we only want XMLRPC download if movie is not in stack,
                    ## you can only retreive multiple subs in zip
    result = False
  else:
    subtitle = os.path.join(__temp__, "%s.%s" %(str(uuid.uuid4()), format))
    try:
      result = OSDBServer().download(id, subtitle)
    except:
      log( __name__, "failed to connect to service for subtitle download")
      return subtitle_list
  if not result:
    log( __name__,"Download Using HTTP")
    zip = os.path.join( __temp__, "OpenSubtitles.zip")
    f = urllib.urlopen(url)
    if not os.path.exists( __temp__ ):
        os.mkdir( __temp__, mode=0o775 )
    with open(zip, "wb") as subFile:
      subFile.write(f.read())
    subFile.close()
    xbmc.sleep(500)
    xbmc.executebuiltin(('XBMC.Extract("%s","%s")' % (zip,__temp__,)).encode('utf-8'), True)
    for file in xbmcvfs.listdir(zip)[1]:
      file = os.path.join(__temp__, file)
      if (os.path.splitext( file )[1] in exts):
        subtitle_list.append(file)
  else:
    subtitle_list.append(subtitle)

  if xbmcvfs.exists(subtitle_list[0]):
    return subtitle_list

def takeTitleFromFocusedItem():
    labelMovieTitle = xbmc.getInfoLabel("ListItem.OriginalTitle")
    labelYear = xbmc.getInfoLabel("ListItem.Year")
    labelTVShowTitle = xbmc.getInfoLabel("ListItem.TVShowTitle")
    labelSeason = xbmc.getInfoLabel("ListItem.Season")
    labelEpisode = xbmc.getInfoLabel("ListItem.Episode")
    labelType = xbmc.getInfoLabel("ListItem.DBTYPE")  #movie/tvshow/season/episode
    isItMovie = labelType == 'movie' or xbmc.getCondVisibility("Container.Content(movies)")
    isItEpisode = labelType == 'episode' or xbmc.getCondVisibility("Container.Content(episodes)")

    title = 'SearchFor...'
    if isItMovie and labelMovieTitle and labelYear:
        title = labelMovieTitle + " " + labelYear
    elif isItEpisode and labelTVShowTitle and labelSeason and labelEpisode:
        title = ("%s S%.2dE%.2d" % (labelTVShowTitle, int(labelSeason), int(labelEpisode)))

    return title

def get_params(string=""):
  param=[]
  if string == "":
    paramstring=sys.argv[2]
  else:
    paramstring=string
  if len(paramstring)>=2:
    params=paramstring
    cleanedparams=params.replace('?','')
    if (params[len(params)-1]=='/'):
      params=params[0:len(params)-2]
    pairsofparams=cleanedparams.split('&')
    param={}
    for i in range(len(pairsofparams)):
      splitparams={}
      splitparams=pairsofparams[i].split('=')
      if (len(splitparams))==2:
        param[splitparams[0]]=splitparams[1]

  return param

def charset_detect(filename):
    with open(filename,'rb') as fi:
        rawdata = fi.read()
    encoding = chardet.detect(rawdata)['encoding']
    if encoding.lower() == 'gb2312':  # Decoding may fail using GB2312
        encoding = 'gbk'
    return encoding


def merge(file, payload):
    subs=[]
    for sub in zip(file, payload):
      subo = pysubs2.load(sub[0], encoding=charset_detect(sub[0]))
      for line in subo:
        line.start += sub[1]['offset'] * 100
        line.end += sub[1]['offset'] * 100
      subs.append(subo)
    ass = os.path.join(__temp__, "%s.ass" %(str(uuid.uuid4())))
    top_style = pysubs2.SSAStyle()
    bottom_style=subs[0].styles["Default"].copy()
    top_style.alignment=8
    top_style.fontsize= int(__addon__.getSetting('top_fontsize'))
    if(__addon__.getSetting('top_bold') == 'true'):
      top_style.bold = 1
    top_style.fontname = str(__addon__.getSetting('top_font'))

    if (__addon__.getSetting('top_color') == 'Yellow'):
      top_style.primarycolor=pysubs2.Color(255, 255, 0, 0)
    elif (__addon__.getSetting('top_color') == 'White'):
      top_style.primarycolor=pysubs2.Color(255, 255, 255, 0)
      top_style.secondarycolor=pysubs2.Color(255,255,255,0)
    if (__addon__.getSetting('top_background') == 'true'):
      top_style.backcolor=pysubs2.Color(0,0,0,128)
      top_style.outlinecolor=pysubs2.Color(0,0,0,128)
      top_style.shadow=0
      top_style.outline=0
      top_style.borderstyle=4
    bottom_style.alignment = 2
    bottom_style.fontsize= str(__addon__.getSetting('bottom_fontsize'))
    if (__addon__.getSetting('bottom_bold') =='true'):
      bottom_style.bold = 1
    bottom_style.fontname = str(__addon__.getSetting('bottom_font'))
    if (__addon__.getSetting('bottom_color') == 'Yellow'):
      bottom_style.primarycolor=pysubs2.Color(255, 255, 0, 0)
    elif (__addon__.getSetting('bottom_color') == 'White'):
      bottom_style.primarycolor=pysubs2.Color(255, 255, 255, 0)
    if (__addon__.getSetting('bottom_background') == 'true'):
      bottom_style.backcolor=pysubs2.Color(0,0,0,128)
      bottom_style.outlinecolor=pysubs2.Color(0,0,0,128)
      bottom_style.shadow=0
      bottom_style.outline=0
      bottom_style.borderstyle=4

    subs[0].styles['top-style'] = top_style
    subs[0].styles['bottom-style'] = bottom_style
    for line in subs[0]:
      line.style= u'bottom-style'
    if len(subs) ==2:
      for line in subs[1]:
        line.style = u'top-style'
        subs[0].append(line)
    subs[0].save(ass,format_='ass')
    return ass

params = get_params()

if params['action'] == 'search' or params['action'] == 'manualsearch':
  log( __name__, "action '%s' called" % params['action'])
  item = {}
  item['temp']               = False
  item['rar']                = False
  item['mansearch']          = False
  item['year']               = xbmc.getInfoLabel("VideoPlayer.Year")                         # Year
  item['season']             = str(xbmc.getInfoLabel("VideoPlayer.Season"))                  # Season
  item['episode']            = str(xbmc.getInfoLabel("VideoPlayer.Episode"))                 # Episode
  item['tvshow']             = normalizeString(xbmc.getInfoLabel("VideoPlayer.TVshowtitle"))  # Show
  item['title']              = normalizeString(xbmc.getInfoLabel("VideoPlayer.OriginalTitle"))# try to get original title
  item['file_original_path'] = xbmc.Player().getPlayingFile()                                 # Full path of a playing file
  item['3let_language']      = [] #['scc','eng']
  PreferredSub		      = params.get('preferredlanguage')

  if 'searchstring' in params:
    item['mansearch'] = True
    item['mansearchstr'] = params['searchstring']

  for lang in unquote(params['languages']).split(","):
    if lang == "Portuguese (Brazil)":
      lan = "pob"
    elif lang == "Greek":
      lan = "ell"
    else:
      lan = xbmc.convertLanguage(lang,xbmc.ISO_639_2)

    item['3let_language'].append(lan)

  if item['title'] == "":
    log( __name__, "VideoPlayer.OriginalTitle not found")
    item['title']  = normalizeString(xbmc.getInfoLabel("VideoPlayer.Title"))      # no original title, get just Title

  if item['episode'].lower().find("s") > -1:                                      # Check if season is "Special"
    item['season'] = "0"                                                          #
    item['episode'] = item['episode'][-1:]

  if ( item['file_original_path'].find("http") > -1 ):
    item['temp'] = True

  elif ( item['file_original_path'].find("rar://") > -1 ):
    item['rar']  = True
    item['file_original_path'] = os.path.dirname(item['file_original_path'][6:])

  elif ( item['file_original_path'].find("stack://") > -1 ):
    stackPath = item['file_original_path'].split(" , ")
    item['file_original_path'] = stackPath[0][8:]

  Search(item)

elif params['action'] == 'download':
  subs=[]
  if(__addon__.getSetting('dualsub_enable') == 'true'):
    payload=json.loads(unquote(params['payload']))
    for sub in payload:
      if (sub['local']):
        subs.append(sub['path'])
      else:
        subs.append(Download(sub["ID"], sub["link"],sub["format"])[0])
    finalfile = merge(subs, payload)
    listitem = xbmcgui.ListItem(label=finalfile)
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=finalfile,listitem=listitem,isFolder=False)
  else:
    if (sub['local']):
      subs.append(sub['path'])
    else:
      subs = Download(params["ID"], params["link"],params["format"])

    for sub in subs:
      listitem = xbmcgui.ListItem(label=sub)
      xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=sub,listitem=listitem,isFolder=False)


xbmcplugin.endOfDirectory(int(sys.argv[1]))
