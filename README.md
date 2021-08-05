# Statwebgen

Obligatory static website generator, used for building my personal website. The project is divided into two parts: the actual website generator (python), and a live refresh server (node.js).

TODO:
* Add mode where statwebgen periodically regenerates the website (Or just use cronjob). This is useful for dynamic functionality. For example, if I want an image updated every five minutes. 
* Add "script folder" which contains scripts to be ran on every website generation/update. Statwebgen will run these scripts too during static website generation.
* statwebgen should be more pipeline oriented, e.g. right now I want to filter all drafts, which is turning out to be somwhat difficult