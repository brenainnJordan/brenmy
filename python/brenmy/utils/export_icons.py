'''
Created on 9 Jun 2018

@author: Bren

export all maya icons to directory

https://simplymaya.com/forum/showthread.php?t=41555

'''


from pymel.core import resourceManager

for item in resourceManager(nameFilter='*'):
    try:
        # Make sure the folder exists before attempting.
        resourceManager(saveAs=(
            item, "E:/dev/python/standalone_tools/examples/icons/maya/{0}".format(item)))
    except:
        # For the cases in which some files do not work for windows, name
        # formatting wise. I'm looking at you 'http:'!
        print item
