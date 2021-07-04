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
    'g'  : '/Glitch',
    'ng' : '/No Glitch',
    'sg' : '/SG',
    'nsg': '/No SG',
    'nu' : '/No Ultra',
    'u'  : '/Ultra'
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
        if msg.content[0] == CMD_PREFIX:
            await self.parseBotCmd(msg)
        return
    
    async def parseBotCmd(self, msg):
        msgContent = msg.content[1:].split()
        if msgContent[0] in {'bkt', 'BKT'}:
            await self.bkt(msg, msgContent)
            
            
            
    async def bkt(self, msg, msgContent):
        try:
            folder = track_folders[msgContent[1]]
        except:
            response = "Unrecognized track."
            await msg.channel.send(response)
            return
        
        folderContents = repo.get_contents(folder)
        
        if folderContents is None:
            response = "Invalid command. Check that this track has the necessary folders."
            await msg.channel.send(response)
            print("Invalid command") #TODO: Print error message to Discord
            return
        
        # Now check for 3lap/flap
        if len(msgContent) < 3:
            response = "Missing 3lap or flap (handle this later)."
            await msg.channel.send(response)
            print("Invalid command") #TODO: Print error message to Discord
            return
        
        if msgContent[2] == '3lap':
            folder += '/3lap'
            folderContents = repo.get_contents(folder)
        elif msgContent[2] == 'flap':
            folder += '/flap'
            folderContents = repo.get_contents(folder)
        else:
            response = "Invalid command. Specify 3lap or flap."
            await msg.channel.send(response)
            return
    
        # Now check if this course has categories
        if len(folderContents) == 1:
            # No categories
            # Replace whitespace with %20
            fileURL = folderContents[0].path.replace(' ', '%20')
            response = "<" + repo.html_url + "/blob/main/" + fileURL + ">"
            await msg.channel.send(response)
            return
        
        try:
            folder += category_folders[msgContent[3]]
        except:
            response = "Invalid category for this track."
            await msg.channel.send(response)
            return
            
        folderContents = repo.get_contents(folder)
        fileURL = folderContents[0].path.replace(' ', '%20')
        response = "<" + repo.html_url + "/blob/main/" + fileURL + ">"
        await msg.channel.send(response)
        return
    

def getRepoObj():
    for repo in g.get_user().get_repos():
        if repo.name == REPO_NAME:
            return repo
    return None

repo = getRepoObj()
client = Bot()
client.run(TOKEN)