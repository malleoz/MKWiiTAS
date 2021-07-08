# Discord-to-Github bot
# Perform GitHub API calls based on parsed chat commands
import os
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
    'NG' : '/No Glitch',
    'nu' : '/No Ultra',
    'NU' : '/No Ultra',
    'ur' : '/Unrestricted',
    'UR' : '/Unrestricted'
}

lap_choices = {
    'flap' : 'Flap',
    'Flap' : 'Flap',
    '3lap' : '3lap'
}

class Bot(discord.Client):
    async def on_ready(self):
        print(f'{self.user} is connected.')
        
    async def on_message(self, msg):
        # Prevent recursion
        if msg.author == self.user:
            return
        # Prevent bot calls from all channels except #mkw-git
        if msg.channel.id != CHANNEL_ID:
            return
        
        '''
        # Example to only allow TASLabz role members
        role = discord.utils.find(lambda r: r.name == 'TASLabz', msg.channel.guild.roles)
        if role in msg.author.roles:
            print("Cool")
        '''
        
        # Check for bot command
        if len(msg.content) > 0 and msg.content[0] == CMD_PREFIX:
            await self.parseBotCmd(msg)
        return
    
    async def parseBotCmd(self, msg):
        msgContent = msg.content[1:].split()
        if msgContent[0] in {'bkt', 'BKT'}:
            await self.bkt(msg, msgContent)
    
    async def decodeTimes(self, binary, offset):
        minutes = int.from_bytes(binary[offset:offset+1], 'big') >> 1
        seconds = (int.from_bytes(binary[offset:offset+2], 'big') & 0x01fc) >> 2
        ms = int.from_bytes(binary[offset+1:offset+3], 'big') & 0x03ff
        
        # Assert format x:xx:xxx
        minutes = str(minutes)
        seconds = str(seconds).zfill(2)
        ms = str(ms).zfill(3)
        return minutes+':'+seconds+'.'+ms
    
    async def get3lapTime(self, file):
        if file.path[-4:] == '.txt':
            # Ghost does not exist in repo
            # Retrieve time from file`
            binary = file.decoded_content.decode().split('\n')
            return binary[0]
            
        binary = file.decoded_content
        
        return await self.decodeTimes(binary, 0x4)
    
    async def getlapTimes(self, file):
        if file.path[-4:] == '.txt':
            # Ghost does not exist in repo
            # Retrieve lap times from file`
            binary = file.decoded_content.decode().split('\n')
            return [str(binary[1]), str(binary[2]), str(binary[3])]
        
        binary = file.decoded_content
        laps = []
        for lap in range (0, 3):
            offset = 0x11  + (lap * 3)
            lapTime = await self.decodeTimes(binary, offset)
            laps.append(lapTime)
        return laps
        
    async def getPlaceholderYTLink(self, file):
        binary = file.decoded_content.decode().split('\n')
        return binary[-2]
    
    async def getCategory(self, folder, folderContents, msgContent):
        if folderContents[0].type == 'dir':
            # We see folders under the course, so we need categories
            try:
                folder += category_folders[msgContent[2]]
            except:
                # Invalid or missing category - Link all ghosts
                return (folder, msgContent)
        
            # Check for empty category folder
            folderContents = repo.get_contents(folder)
            if folderContents is None:
                return (None, None)
            
            # Strip out category
            msgContent = msgContent[0:2] + msgContent[3:]
                
        return (folder, msgContent)
    
    async def getFiles(self, msg, laps, folder):
        files = []
        folderContents = repo.get_contents(folder)
        for content in folderContents:
            if content.type == 'dir':
                temp = await self.getFiles(msg, laps, content.path)
                if temp is not None:
                    files += temp
            elif laps in content.name:
                files.append(content)
        return files
    
    async def parseBKTLinks(self, msg, files):
        track = files[0].path.split('/')[0][4:]
        
        # Embed post
        embed = discord.Embed(title=track, description="BKT", color=0x008800)
        
        #response = f"**{track}**\n"
        last_cat = ''
        value = ''
        for file in files:
            fileDirs = file.path.split('/')
            if len(fileDirs) == 2:
                # There are no categories on this course
                category = 'Unrestricted'
            else:
                category = fileDirs[-2]
            
            # If we have cached one ghost which is a different category from the current ghost,
            # Add embed field for the cached ghost
            if last_cat not in {category, ''}:
                embed.add_field(name=last_cat, value=value, inline=False)
                value = ''
            
            laps = fileDirs[-1][:4]
            time = await self.get3lapTime(file)
            laptimes = await self.getlapTimes(file)
            fileURL = repo.html_url + "/blob/main/" + file.path.replace(' ', '%20') + "?raw=true"
            
            linkText = 'DL'
            
            if file.path[-4:] == '.txt':
                # Remove embed link since not a valid ghost file
                linkText = 'No ghost on repo'
                fileURL = await self.getPlaceholderYTLink(file)
            
            value+=f"{laps} - {time} ({laptimes[0]}, {laptimes[1]}, {laptimes[2]}) [[{linkText}]]({fileURL})\n"
            
            # In order to handle groupings of 3lap+flap for one category field,
            # do one of the following
            if file == files[-1]: # if last ghost, force field add
                embed.add_field(name=category, value=value, inline=False)
            elif last_cat == category: # We looked at 3lap, now looking at flap, done w/ category so add field
                embed.add_field(name=category, value=value, inline=False)
                value = ''
                last_cat = ''
            else: # there may be another ghost for this category so wait to check the next ghost
                last_cat = category
                
        if embed.fields == discord.Embed.Empty:
            return
            
        await msg.channel.send(embed=embed)
    
    async def bkt(self, msg, msgContent):
        # Get track folder
        try:
            track_folder = track_folders[msgContent[1].lower()]
        except:
            return
        
        # Check for empty course folder
        folderContents = repo.get_contents(track_folder)
        if folderContents is None:
            return
        
        (cat_folder, msgContent) = await self.getCategory(track_folder, folderContents, msgContent)
        
        # Handle the case when no 3lap/flap is provided
        try:
            laps = lap_choices[msgContent[2]]
        except:
            laps = ''
        
        # Check if we should get all ghost files
        files = await self.getFiles(msg, laps, cat_folder)
        
        if files == [None]:
            return
            
        # Parse the URLs
        await self.parseBKTLinks(msg, files)

def getRepoObj():
    for repo in g.get_user().get_repos():
        if repo.name == REPO_NAME:
            return repo
    return None

repo = getRepoObj()
client = Bot()
client.run(TOKEN)
