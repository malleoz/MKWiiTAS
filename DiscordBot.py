# Discord-to-Github bot
# Perform GitHub API calls based on parsed chat commands
import os
import re
import discord
from dotenv import load_dotenv
from github import Github

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
GITHUB_ACCESS_TOKEN= os.getenv('GITHUB_ACCESS_TOKEN')
REPO_NAME = 'MKWiiTAS'
repo = None
CMD_PREFIX = '!'

g = Github(GITHUB_ACCESS_TOKEN)

track_folders = {
    'lc'   : '01. Luigi Circuit',
    'mmm'  : '02. Moo Moo Meadows',
    'mg'   : '03. Mushroom Gorge',
    'tf'   : '04. Toad\'s Factory',
    'mc'   : '05. Mario Circuit',
    'cm'   : '06. Coconut Mall',
    'dks'  : '07. DK Summit',
    'wgm'  : '08. Wario\'s Gold Mine',
    'dc'   : '09. Daisy Circuit',
    'kc'   : '10. Koopa Cape',
    'mt'   : '11. Maple Treeway',
    'gv'   : '12. Grumble Volcano',
    'ddr'  : '13. Dry Dry Ruins',
    'mh'   : '14. Moonview Highway',
    'bc'   : '15. Bowser\'s Castle',
    'rr'   : '16. Rainbow Road',
    'rpb'  : '17. GCN Peach Beach',
    'ryf'  : '18. DS Yoshi Falls',
    'rgv2' : '19. SNES Ghost Valley 2',
    'rmr'  : '20. N64 Mario Raceway',
    'rsl'  : '21. N64 Sherbet Land',
    'rsgb' : '22. GBA Shy Guy Beach',
    'rds'  : '23. DS Delfino Square',
    'rws'  : '24. GCN Waluigi Stadium',
    'rdh'  : '25. DS Desert Hills',
    'rbc3' : '26. GBA Bowser Castle 3',
    'rdkjp': '27. N64 DK\'s Jungle Parkway',
    'rmc'  : '28. GCN Mario Circuit',
    'rmc3' : '29. SNES Mario Circuit 3',
    'rpg'  : '30. DS Peach Gardens',
    'rdkm' : '31. GCN DK Mountain',
    'rbc'  : '32. N64 Bowser\'s Castle'
}

category_folders = {
    'ng' : '/No Glitch',
    'nu' : '/No Ultra',
    'ur' : '/Unrestricted',
}

lap_choices = {
    'flap' : 'Flap',
    '3lap' : '3lap'
}

class Bot(discord.Client):
    async def on_ready(self):
        print(f'{self.user} is connected.')
    
    async def cmdHelp(self, cmd):
        response = ''
        if cmd in 'bkt':
             response += f'```css\n!bkt track [category] [laps]\n```'
        
        return response
    
    async def on_message(self, msg):
        # Prevent recursion
        if msg.author == self.user:
            return
            
        # Prevent bot calls from all channels except #mkw-git
        if msg.channel.id != CHANNEL_ID:
            return
        
        # Check for bot command
        if len(msg.content) > 0 and msg.content[0] == CMD_PREFIX:
            await self.parseBotCmd(msg)
        
        return
    
    async def parseBotCmd(self, msg):
        msgContent = msg.content[1:].split()
        cmd = msgContent[0].lower()
        
        if cmd == 'bkt':
            return await self.bkt(msg, msgContent)
    
    async def decodeTimes(self, binary, offset):
        minutes = int.from_bytes(binary[offset:offset+1], 'big') >> 1
        seconds = (int.from_bytes(binary[offset:offset+2], 'big') & 0x01fc) >> 2
        ms      = int.from_bytes(binary[offset+1:offset+3], 'big') & 0x03ff
        
        # Assert format x:xx:xxx
        minutes = str(minutes)
        seconds = str(seconds).zfill(2) #Pad with 0s
        ms = str(ms).zfill(3) # Pad with 0s
        return minutes+':'+seconds+'.'+ms
    
    async def getFileBinary(self, file):
        try:
            return file.decoded_content
        except:
            return None
    
    async def get3lapTime(self, binary, fileExtension):
        if fileExtension == 'txt':
            # Ghost does not exist in repo
            # Retrieve time from file
            return binary.decode().split('\n')[0]
        
        return await self.decodeTimes(binary, 0x4)
    
    async def getlapTimes(self, binary, fileExtension):
        if fileExtension == 'txt':
            # Ghost does not exist in repo
            # Retrieve lap times from file`
            binary = binary.decode().split('\n')
            return [str(binary[1]), str(binary[2]), str(binary[3])]
        
        # Decode lap time in binary at 0x11 + (x*3)
        # where x is the lap #
        # and 3 represents the # of bytes for each lap's time structure
        return [await self.decodeTimes(binary, 0x11 + (x * 3)) for x in range(0, 3)]
        
    async def getYTLink(self, file, category, laps):
        try:
            binary = file.decoded_content.decode()
        except:
            return '' # Empty string prevents link creation
            
        for line in binary.split('\n'):
            if all(x in line for x in [category, laps]):
                    return line.split()[-1]
        return '' # Empty string prevents link creation
    
    async def getCategory(self, folder, folderContents, msgContent):
        if folderContents[0].type == 'dir':
            # We see folders under the course, so we need categories
            try:
                # Append this subfolder to the folder path
                folder += category_folders[msgContent[2].lower()]
                
                # Strip out category (to indistinguish this from cmd with no category specified)
                msgContent = msgContent[0:2] + msgContent[3:]
            except:
                # Invalid or missing category - Link all ghosts
                pass
      
        return (folder, msgContent)
    
    async def getFiles(self, msg, laps, folder):
        files = []
        folderContents = repo.get_contents(folder)
        for content in folderContents:
            if content.type == 'dir':
                # Recurse down to this folder (category)
                temp = await self.getFiles(msg, laps, content.path)
                if temp is not None:
                    files += temp
            elif laps in content.name and content.name != 'YTLookup.txt':
                files.append(content)
        return files
        
    async def getFastestLapIndex(self, laptimes):
        # Parse laptime string as seconds for comparison
        lapSeconds = []
        for i in range(0, len(laptimes)):
            lap = laptimes[i]
            laptime = 0
            if lap == 'Unknown' or lap == 'N/A':
                continue
                
            # Separate lap times by minutes,seconds,ms
            lapComponents = re.split(':|\.', lap)
            
            if len(lapComponents) == 3: # Minutes
                laptime += (60 * int(lapComponents[0]))
                lapComponents.pop(0)
            if len(lapComponents) == 2: # Seconds
                laptime += (int(lapComponents[0]))
                lapComponents.pop(0)
            if len(lapComponents) == 1: # Milliseconds
                laptime += (.001 * int(lapComponents[0]))
                
            # Store [time, index]
            lapSeconds.append([laptime, i])
        
        # Sort laps based off of time
        lapSeconds.sort(key = lambda x: x[0])
        try:
            return lapSeconds[0][1]
        except:
            return -1 # No lap times provided
    
    async def bktEmbed(self, msg, files):
        track = files[0].path.split('/')[0][4:]
        
        # Embed obj
        embed = discord.Embed(title=track, description="BKTs", color=0x89DA72)
        
        last_cat = ''
        value = ''
        
        for bkt in files:
            fileDirs = bkt.path.split('/')
            
            # Check if no categories on this course
            category = 'Unrestricted' if len(fileDirs) == 2 else fileDirs[-2]
            
            # Check if the last ghost we checked was in a different category
            # If so, we want to print them separately in the embed post
            if last_cat not in {category, ''}:
                embed.add_field(name=last_cat, value=value, inline=False)
                value = ''
            
            binary = await self.getFileBinary(bkt)
            fileExtension = bkt.path.split('.')[-1]
            time = await self.get3lapTime(binary, fileExtension)
            laps = fileDirs[-1][:4]
            laptimes = await self.getlapTimes(binary, fileExtension)
            
            rkgLink = repo.html_url + "/blob/main/" + bkt.path.replace(' ', '%20') + "?raw=true"
            linkText = '[DL]'
            ytLookupFile = repo.get_contents(fileDirs[0])[-1]
            ytLink = await self.getYTLink(ytLookupFile, category, laps)
            
            if bkt.path[-4:] == '.txt':
                # Remove embed link since not a valid ghost file
                rkgLink = ''
                linkText = ''
            
            value += f"[{laps}]({ytLink}) - "
            
            if laps == '3lap':
                if time == "No TAS Yet":
                    value+=time
                else:
                    value+=f"{time} ({laptimes[0]}, {laptimes[1]}, {laptimes[2]})"
            elif laps == 'Flap':
                print(bkt.path)
                fastLapIndex = await self.getFastestLapIndex(laptimes)
                if fastLapIndex == -1:
                    # No laps provided
                    value+="No TAS Yet"
                else:
                    value+=f"{laptimes[fastLapIndex]} (Final Time: {time})"
            
            value += f" [{linkText}]({rkgLink})\n"

            last_cat = category
        
        # Since we're done iterating the list of ghost files, add the last ghost
        embed.add_field(name=category, value=value, inline=False)
        
        if embed.fields == discord.Embed.Empty:
            return
        await msg.channel.send(embed=embed)
    
    async def printTracks(self, msg):
        response = '```LC     MC     DC     DDR\n' \
                      'MMM    CM     KC     MH\n' \
                      'MG     DKS    MT     BC\n' \
                      'TF     WGM    GV     RR\n\n' \
                      'rPB    rSL    rDH    rMC3\n' \
                      'rYF    rSGB   rBC3   rPG\n' \
                      'rGV2   rDS    rDKJP  rDKM\n' \
                      'rMR    rWS    rMC    rBC```'
        return response
    
    async def embedError(self, msg, error, cmd, details):
        cmdHelp = await self.cmdHelp(cmd)
        if details == 'track':
            cmdHelp += "\nUse one of the following:\n" + await self.printTracks(msg)
            
        embed = discord.Embed(title=error, description=cmdHelp, color=0xC13353)
        await msg.channel.send(embed=embed)
    
    async def bkt(self, msg, msgContent):
        # Get track folder
        try:
            track_folder = track_folders[msgContent[1].lower()]
        except:
            if len(msgContent) == 1:
                error = "No track provided."
                await self.embedError(msg, error, 'bkt', 'track')
                return
        
        folderContents = repo.get_contents(track_folder)
        
        # Get category (if provided) and remove it from the msgContent to handle both cases the same way
        (cat_folder, msgContent) = await self.getCategory(track_folder, folderContents, msgContent)
        
        # Handle the case when no 3lap/flap is provided
        try:
            laps = lap_choices[msgContent[2].lower()]
        except:
            laps = ''
        
        # Get all relevant ghost files
        files = await self.getFiles(msg, laps, cat_folder)
            
        # Parse the URLs
        await self.bktEmbed(msg, files)

def getRepoObj():
    for repo in g.get_user().get_repos():
        if repo.name == REPO_NAME:
            return repo
    return None

repo = getRepoObj()
client = Bot()
client.run(TOKEN)
