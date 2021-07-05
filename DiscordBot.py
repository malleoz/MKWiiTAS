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
    'LC'   : '01. Luigi Circuit',
    'MMM'  : '02. Moo Moo Meadows',
    'MG'   : '03. Mushroom Gorge',
    'TF'   : '04. Toad\'s Factory',
    'MC'   : '05. Mario Circuit',
    'CM'   : '06. Coconut Mall',
    'DKS'  : '07. DK Summit',
    'WGM'  : '08. Wario\'s Gold Mine',
    'DC'   : '09. Daisy Circuit',
    'KC'   : '10. Koopa Cape',
    'MT'   : '11. Maple Treeway',
    'GV'   : '12. Grumble Volcano',
    'DDR'  : '13. Dry Dry Ruins',
    'MH'   : '14. Moonview Highway',
    'BC'   : '15. Bowser\'s Castle',
    'RR'   : '16. Rainbow Road',
    'rPB'  : '17. GCN Peach Beach',
    'rYF'  : '18. DS Yoshi Falls',
    'rGV2' : '19. SNES Ghost Valley 2',
    'rMR'  : '20. N64 Mario Raceway',
    'rSL'  : '21. N64 Sherbet Land',
    'rSGB' : '22. GBA Shy Guy Beach',
    'rDS'  : '23. DS Delfino Square',
    'rWS'  : '24. GCN Waluigi Stadium',
    'rDH'  : '25. DS Desert Hills',
    'rBC3' : '26. GBA Bowser Castle 3',
    'rDKJP': '27. N64 DK\'s Jungle Parkway',
    'rMC'  : '28. GCN Mario Circuit',
    'rMC3' : '29. SNES Mario Circuit 3',
    'rPG'  : '30. DS Peach Gardens',
    'rDKM' : '31. GCN DK Mountain',
    'rBC'  : '32. N64 Bowser\'s Castle'
}

category_folders = {
    'ng' : '/No Glitch',
    'NG' : '/No Glitch',
    'nu' : '/No Ultra',
    'NU' : '/No Ultra',
    'ur' : '/Unrestricted',
    'UR' : '/Unrestricted'
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
        
        # Check for bot command
        if len(msg.content) > 0 and msg.content[0] == CMD_PREFIX:
            await self.parseBotCmd(msg)
        return
    
    async def parseBotCmd(self, msg):
        msgContent = msg.content[1:].split()
        if msgContent[0] in {'bkt', 'BKT'}:
            await self.bkt(msg, msgContent)  
    
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
        for subfolder in folderContents:
            temp = await self.getFile(msg, laps, subfolder.path)
            if temp is not None:
                files.append(temp)
        print(files)
        return files
    
    async def getFile(self, msg, laps, folder):
        # Check that relevant file is there
        folderContents = repo.get_contents(folder)
        for file in folderContents:
            if laps in file.name:
                return file
        return
        
    async def bkt(self, msg, msgContent):
        # Get track folder
        try:
            folder = track_folders[msgContent[1]]
        except:
            return
        
        # Check for empty course folder
        folderContents = repo.get_contents(folder)
        if folderContents is None:
            return
        
        (folder, msgContent) = await self.getCategory(folder, folderContents, msgContent)
        
        # Check if we should get all ghost files
        if repo.get_contents(folder)[0].type == 'dir':
            files = await self.getFiles(msg, msgContent[2], folder)
        else:
            files = await self.getFile(msg, msgContent[2], folder)
            files = [files]
        
        if files == [None]:
            return
            
        # Parse the URLs
        response = ""
        for file in files:
            category = file.path.split('/')[-2]
            laps = file.path.split('/')[-1][:4]
            fileURL = repo.html_url + "/blob/main/" + file.path.replace(' ', '%20')
            response = response + f"**{category} {laps}:** <{fileURL}>\n"
        if response == "":
            return
        await msg.channel.send(response)
    

def getRepoObj():
    for repo in g.get_user().get_repos():
        if repo.name == REPO_NAME:
            return repo
    return None

repo = getRepoObj()
client = Bot()
client.run(TOKEN)