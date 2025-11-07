Now we come to the final change that we will make to the high-level design of cIMG.
File formats tend to give the parsing program a number of directives to carry out different actions.
In HTML files, for example, each tag is a directive that causes the rendering engine to take action.
Image files are similar.
We'll start our exploration of this relationship between the format and the parser by extending cIMG with a similar concept.
